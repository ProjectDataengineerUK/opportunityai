from fastapi import APIRouter, HTTPException, Query
from services.firestore import FirestoreService
from services.gemini import GeminiClient
from agents.classifier import Classifier
from agents.evaluator import Evaluator
from agents.proposal_generator import ProposalGenerator
from models import RawJob
from config import get_config

router = APIRouter(prefix="/api")
_firestore: FirestoreService | None = None


def get_firestore() -> FirestoreService:
    global _firestore
    if _firestore is None:
        _firestore = FirestoreService(get_config().gcp_project_id)
    return _firestore


def _make_gemini(model_key: str = "default") -> GeminiClient:
    config = get_config()
    model = config.gemini.default_model if model_key == "default" else config.gemini.advanced_model
    return GeminiClient(project_id=config.gcp_project_id, location=config.gcp_location, model=model)


@router.get("/opportunities")
async def list_opportunities(
    area: str | None = Query(default=None),
    decision: str | None = Query(default=None),
    source: str | None = Query(default=None),
    limit: int = Query(default=200, le=500),
):
    return get_firestore().list_opportunities(area=area, decision=decision, source=source, limit=limit)


@router.get("/opportunities/{opportunity_id}")
async def get_opportunity(opportunity_id: str):
    doc = get_firestore().get_opportunity(opportunity_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return doc


@router.post("/opportunities/{opportunity_id}/recalculate")
async def recalculate_opportunity(opportunity_id: str):
    firestore_svc = get_firestore()
    doc = firestore_svc.get_opportunity(opportunity_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    gemini = _make_gemini("default")
    classifier = Classifier(gemini)
    evaluator = Evaluator(gemini, get_config())

    raw = RawJob(
        external_id=doc["external_id"],
        source=doc["source"],
        title=doc["title"],
        description=doc["description"],
        budget_min=doc.get("budget_min"),
        budget_max=doc.get("budget_max"),
        budget_currency=doc.get("budget_currency"),
        url=doc["url"],
        language=doc.get("language", "en"),
        raw_data=doc.get("raw_data", {}),
    )

    area = classifier.classify(raw.title, raw.description)
    opportunity = evaluator.evaluate(raw, area)

    updated_fields = {
        "area": opportunity.area,
        "score": opportunity.score,
        "score_breakdown": opportunity.score_breakdown.model_dump(),
        "decision": opportunity.decision,
        "summary": opportunity.summary,
        "skills_required": opportunity.skills_required,
    }
    firestore_svc.update_opportunity(opportunity_id, updated_fields)

    return {**doc, **updated_fields, "id": opportunity_id}


@router.post("/opportunities/{opportunity_id}/proposal")
async def generate_proposal(opportunity_id: str):
    firestore_svc = get_firestore()
    doc = firestore_svc.get_opportunity(opportunity_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    gemini = _make_gemini("advanced")
    generator = ProposalGenerator(gemini, get_config())

    result = generator.generate(
        title=doc["title"],
        description=doc["description"],
        area=doc.get("area", ""),
        language=doc.get("language", "en"),
        skills_required=doc.get("skills_required", []),
        budget_min=doc.get("budget_min"),
        summary=doc.get("summary", ""),
    )

    firestore_svc.update_opportunity(opportunity_id, {
        "proposal": result.proposal,
        "suggested_price": result.suggested_price,
        "estimated_hours": result.estimated_hours,
    })

    return {
        "proposal": result.proposal,
        "suggested_price": result.suggested_price,
        "estimated_hours": result.estimated_hours,
    }
