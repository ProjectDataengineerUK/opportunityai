import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from services.firestore import FirestoreService
from services.gemini import GeminiClient
from agents.classifier import Classifier
from agents.evaluator import Evaluator
from agents.proposal_generator import ProposalGenerator
from models import RawJob, ProposalOutcome
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

    area = await asyncio.to_thread(classifier.classify, raw.title, raw.description)
    opportunity = await asyncio.to_thread(evaluator.evaluate, raw, area)

    updated = {
        "area": opportunity.area,
        "score": opportunity.score,
        "score_breakdown": opportunity.score_breakdown.model_dump(),
        "decision": opportunity.decision,
        "summary": opportunity.summary,
        "skills_required": opportunity.skills_required,
    }
    firestore_svc.update_opportunity(opportunity_id, updated)

    return {**doc, **updated, "id": opportunity_id}


@router.post("/opportunities/{opportunity_id}/proposal")
async def generate_proposal(opportunity_id: str):
    firestore_svc = get_firestore()
    doc = firestore_svc.get_opportunity(opportunity_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    gemini = _make_gemini("advanced")
    generator = ProposalGenerator(gemini, get_config())

    result = await asyncio.to_thread(
        generator.generate,
        title=doc["title"],
        description=doc["description"],
        area=doc.get("area", ""),
        language=doc.get("language", "en"),
        skills_required=doc.get("skills_required", []),
        budget_min=doc.get("budget_min"),
        summary=doc.get("summary", ""),
    )

    update = {
        "proposal": result.proposal,
        "proposal_direct": result.proposal_direct,
        "proposal_consultive": result.proposal_consultive,
        "suggested_price": result.suggested_price,
        "estimated_hours": result.estimated_hours,
    }
    firestore_svc.update_opportunity(opportunity_id, update)

    return update


@router.post("/opportunities/{opportunity_id}/outcome")
async def record_outcome(opportunity_id: str, body: ProposalOutcome):
    firestore_svc = get_firestore()
    if not firestore_svc.get_opportunity(opportunity_id):
        raise HTTPException(status_code=404, detail="Opportunity not found")

    outcome_data = body.model_dump()
    outcome_data["recorded_at"] = datetime.now(timezone.utc).isoformat()
    firestore_svc.save_outcome(outcome_data)

    return {"status": "recorded"}


@router.get("/stats/win-rate")
async def get_win_rate():
    firestore_svc = get_firestore()
    outcomes = firestore_svc.list_outcomes()

    total = len(outcomes)
    if total == 0:
        return {"win_rate": None, "total": 0, "won": 0, "lost": 0, "no_response": 0}

    won = sum(1 for o in outcomes if o.get("outcome") == "ganhou")
    lost = sum(1 for o in outcomes if o.get("outcome") == "perdeu")
    no_resp = sum(1 for o in outcomes if o.get("outcome") == "sem_resposta")

    return {
        "win_rate": round(won / total * 100, 1),
        "total": total,
        "won": won,
        "lost": lost,
        "no_response": no_resp,
    }
