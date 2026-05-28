from pydantic import BaseModel
from services.gemini import GeminiClient
from config import AppConfig


class ProposalResult(BaseModel):
    proposal: str          # proposta completa no idioma da vaga
    suggested_price: float | None  # valor sugerido em USD
    estimated_hours: int | None    # horas estimadas


class ProposalGenerator:
    def __init__(self, gemini: GeminiClient, config: AppConfig):
        self.gemini = gemini
        self.config = config

    def generate(
        self,
        title: str,
        description: str,
        area: str,
        language: str,
        skills_required: list[str],
        budget_min: float | None,
        summary: str,
    ) -> ProposalResult:
        profile = self.config.user_profile
        lang_note = "em português" if language == "pt" else "in English"
        budget_str = f"USD {budget_min}" if budget_min else "não informado"

        prompt = f"""Gere uma proposta freelance personalizada {lang_note} para a vaga abaixo.

PERFIL DO FREELANCER:
Skills: {', '.join(profile['skills'])}
Valor mínimo: USD {profile['min_budget_usd']}

VAGA:
Título: {title}
Área: {area}
Descrição: {description[:1200]}
Skills exigidas: {', '.join(skills_required) if skills_required else 'não especificadas'}
Orçamento do cliente: {budget_str}
Análise: {summary}

INSTRUÇÕES:
- Proposta direta, profissional e personalizada para os requisitos específicos desta vaga
- Demonstre entendimento real do problema do cliente
- Mencione as skills relevantes do perfil sem inventar projetos específicos
- Tom confiante, sem ser arrogante
- Máximo 3 parágrafos curtos
- Sugira um preço realista em USD baseado no escopo descrito
- Estime horas de trabalho se possível deduzir do escopo"""

        return self.gemini.generate_structured(prompt, ProposalResult)
