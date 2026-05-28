from datetime import datetime, timezone
from pydantic import BaseModel
from models import Opportunity, RawJob, ScoreBreakdown
from services.gemini import GeminiClient
from config import AppConfig
from agents.classifier import Area


class EvaluationResult(BaseModel):
    skill_match: float
    budget_score: float
    close_chance: float
    competition: float
    clarity: float
    summary: str
    skills_required: list[str]


class Evaluator:
    def __init__(self, gemini: GeminiClient, config: AppConfig):
        self.gemini = gemini
        self.config = config

    def evaluate(self, job: RawJob, area: Area) -> Opportunity:
        profile = self.config.user_profile
        weights = self.config.score_weights
        thresholds = self.config.decision_thresholds

        budget_str = "não informado"
        if job.budget_min is not None:
            budget_str = f"{job.budget_currency or 'USD'} {job.budget_min}"
            if job.budget_max:
                budget_str += f" – {job.budget_max}"

        prompt = f"""Avalie esta vaga freelance para o perfil abaixo. Seja rigoroso e realista.

PERFIL DO FREELANCER:
Skills: {', '.join(profile['skills'])}
Valor mínimo: USD {profile['min_budget_usd']}
Idiomas: {', '.join(profile['languages'])}

VAGA:
Área classificada: {area}
Título: {job.title}
Descrição: {job.description[:1200]}
Orçamento: {budget_str}

Avalie cada critério de 0.0 a 100.0:
- skill_match: % de skills exigidas que o freelancer possui
- budget_score: 100 se orçamento >= mínimo, 0 se não informado ou abaixo
- close_chance: estimativa de chance de fechar (histórico implícito, clareza, urgência)
- competition: 100 se vaga nova/pouco concorrida, 0 se muito disputada
- clarity: quão bem descrita e estruturada é a vaga (0=vaga demais, 100=perfeita)

Gere também:
- summary: resumo de 2-4 linhas em português sobre a vaga e por que vale/não vale aplicar
- skills_required: lista das skills técnicas exigidas na vaga"""

        result = self.gemini.generate_structured(prompt, EvaluationResult)

        w = weights
        score = round(
            result.skill_match * w["skill_match"]
            + result.budget_score * w["budget"]
            + result.close_chance * w["close_chance"]
            + result.competition * w["competition"]
            + result.clarity * w["clarity"],
            1,
        )

        if score >= thresholds["aplicar"]:
            decision = "APLICAR"
        elif score >= thresholds["avaliar"]:
            decision = "AVALIAR"
        else:
            decision = "IGNORAR"

        return Opportunity(
            external_id=job.external_id,
            source=job.source,
            title=job.title,
            description=job.description,
            budget_min=job.budget_min,
            budget_max=job.budget_max,
            budget_currency=job.budget_currency,
            url=job.url,
            area=area,
            score=score,
            score_breakdown=ScoreBreakdown(
                skill_match=result.skill_match,
                budget=result.budget_score,
                close_chance=result.close_chance,
                competition=result.competition,
                clarity=result.clarity,
            ),
            decision=decision,
            summary=result.summary,
            skills_required=result.skills_required,
            language=job.language,
            collected_at=datetime.now(timezone.utc),
            raw_data=job.raw_data,
        )
