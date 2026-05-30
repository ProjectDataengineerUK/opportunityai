from pydantic import BaseModel
from datetime import datetime
from typing import Literal

SourceName = Literal["remoteok", "remotive", "freelancer", "upwork", "workana"]


class ScoreBreakdown(BaseModel):
    skill_match: float
    budget: float
    close_chance: float
    competition: float
    clarity: float


class RawJob(BaseModel):
    external_id: str
    source: SourceName
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
    source: SourceName
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

    # Fraude
    fraud_risk: float = 0.0
    fraud_flags: list[str] = []

    # Análise do cliente
    client_score: float = 0.0
    client_hire_rate: float | None = None
    client_payment_verified: bool = False
    client_total_spent: float | None = None

    # Competição & timing
    proposals_count: int | None = None
    posted_at: datetime | None = None
    urgency: Literal["quente", "normal", "frio"] = "normal"

    # Propostas
    proposal: str | None = None          # legado — proposta única
    proposal_direct: str | None = None   # estilo direto (2 parágrafos)
    proposal_consultive: str | None = None  # estilo consultivo (3 parágrafos)
    suggested_price: float | None = None
    estimated_hours: int | None = None

    # Aprendizado
    win_probability: float | None = None


class ProposalOutcome(BaseModel):
    opportunity_id: str
    outcome: Literal["ganhou", "perdeu", "sem_resposta"]
    recorded_at: datetime
    notes: str = ""


class CollectResponse(BaseModel):
    collected: int
    saved: int
    skipped_duplicate: int
    skipped_irrelevant: int
    skipped_fraud: int = 0
