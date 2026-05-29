import asyncio
import logging
from fastapi import APIRouter
from agents.collector import Collector
from agents.classifier import Classifier
from agents.evaluator import Evaluator
from agents.fraud_detector import FraudDetector
from agents.client_analyzer import ClientAnalyzer
from services.firestore import FirestoreService
from services.gemini import GeminiClient
from services.telegram import TelegramNotifier
from models import CollectResponse, RawJob
from config import get_config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

MAX_CONCURRENT = 8  # Gemini calls in parallel


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
    client_analyzer = ClientAnalyzer()
    telegram = TelegramNotifier()
    collector = Collector(config)

    raw_jobs = await collector.collect_all()

    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    lock = asyncio.Lock()
    counters = {"saved": 0, "dup": 0, "irrel": 0, "fraud": 0, "error": 0}
    new_opps = []

    async def process_job(job: RawJob):
        async with semaphore:
            try:
                if await asyncio.to_thread(firestore_svc.exists, job.external_id):
                    async with lock:
                        counters["dup"] += 1
                    return

                area = await asyncio.to_thread(classifier.classify, job.title, job.description)

                if area == "Irrelevante":
                    async with lock:
                        counters["irrel"] += 1
                    return

                fraud = await asyncio.to_thread(
                    fraud_detector.analyze, job.title, job.description, job.budget_min, job.budget_max
                )

                if fraud.risk_score > 80:
                    async with lock:
                        counters["fraud"] += 1
                    return

                client = client_analyzer.analyze(job)
                opportunity = await asyncio.to_thread(evaluator.evaluate, job, area)

                opportunity.fraud_risk = fraud.risk_score
                opportunity.fraud_flags = fraud.flags
                opportunity.client_score = client.score
                opportunity.client_hire_rate = client.hire_rate
                opportunity.client_payment_verified = client.payment_verified
                opportunity.client_total_spent = client.total_spent
                opportunity.proposals_count = client.proposals_count
                opportunity.posted_at = client.posted_at
                opportunity.urgency = client.urgency

                await asyncio.to_thread(firestore_svc.save, opportunity)
                async with lock:
                    counters["saved"] += 1
                    new_opps.append(opportunity)

            except Exception as exc:
                logger.error("job %s failed: %s", job.external_id, exc)
                async with lock:
                    counters["error"] += 1

    await asyncio.gather(*[process_job(job) for job in raw_jobs])

    await telegram.notify_top_opportunities(new_opps)

    return CollectResponse(
        collected=len(raw_jobs),
        saved=counters["saved"],
        skipped_duplicate=counters["dup"],
        skipped_irrelevant=counters["irrel"],
        skipped_fraud=counters["fraud"],
    )
