from pydantic import BaseModel
from datetime import datetime
from typing import Literal


class ScoreBreakdown(BaseModel):
    skill_match: float
    budget: float
    close_chance: float
    competition: float
    clarity: float


class RawJob(BaseModel):
    external_id: str
    source: Literal["remoteok", "remotive", "freelancer"]
    title: str
    description: str
    budget_min: float | None = None
    budget_max: float | None = None
    budget_currency: str | None = None
    url: str
    language: str = "en"
    raw_data: dict = {}


class Opportunity(BaseModel):
    id: str | None = None
    external_id: str
    source: Literal["remoteok", "remotive", "freelancer"]
    title: str
    description: str
    budget_min: float | None = None
    budget_max: float | None = None
    budget_currency: str | None = None
    url: str
    area: Literal["IA", "Dados", "Python", "Backend", "Automação", "Cloud", "Irrelevante"]
    score: float
    score_breakdown: ScoreBreakdown
    decision: Literal["APLICAR", "AVALIAR", "IGNORAR"]
    summary: str
    skills_required: list[str] = []
    language: str
    collected_at: datetime
    raw_data: dict = {}
    # Fase 2
    fraud_risk: float = 0.0
    fraud_flags: list[str] = []
    proposal: str | None = None
    suggested_price: float | None = None
    estimated_hours: int | None = None


class CollectResponse(BaseModel):
    collected: int
    saved: int
    skipped_duplicate: int
    skipped_irrelevant: int
    skipped_fraud: int = 0
