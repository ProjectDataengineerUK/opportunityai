from fastapi import APIRouter
from agents.collector import Collector
from agents.classifier import Classifier
from agents.evaluator import Evaluator
from agents.fraud_detector import FraudDetector
from services.firestore import FirestoreService
from services.gemini import GeminiClient
from models import CollectResponse
from config import get_config

router = APIRouter(prefix="/api")


@router.post("/collect", response_model=CollectResponse)
async def collect_opportunities():
    config = get_config()
    gemini = GeminiClient(
        project_id=config.gcp_project_id,
        location=config.gcp_location,
        model=config.gemini.default_model,
    )
    firestore_svc = FirestoreService(config.gcp_project_id)
    classifier = Classifier(gemini)
    evaluator = Evaluator(gemini, config)
    fraud_detector = FraudDetector(gemini)
    collector = Collector(config)

    raw_jobs = await collector.collect_all()

    saved = skipped_dup = skipped_irrelevant = skipped_fraud = 0

    for job in raw_jobs:
        if firestore_svc.exists(job.external_id):
            skipped_dup += 1
            continue

        area = classifier.classify(job.title, job.description)

        if area == "Irrelevante":
            skipped_irrelevant += 1
            continue

        fraud = fraud_detector.analyze(job.title, job.description, job.budget_min, job.budget_max)

        if fraud.risk_score > 80:
            skipped_fraud += 1
            continue

        opportunity = evaluator.evaluate(job, area)
        opportunity.fraud_risk = fraud.risk_score
        opportunity.fraud_flags = fraud.flags

        firestore_svc.save(opportunity)
        saved += 1

    return CollectResponse(
        collected=len(raw_jobs),
        saved=saved,
        skipped_duplicate=skipped_dup,
        skipped_irrelevant=skipped_irrelevant,
        skipped_fraud=skipped_fraud,
    )
