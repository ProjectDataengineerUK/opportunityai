from pydantic import BaseModel
from services.gemini import GeminiClient
from config import AppConfig


class ProposalResult(BaseModel):
    proposal: str
    proposal_direct: str
    proposal_consultive: str
    suggested_price: float | None
    estimated_hours: int | None


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

        prompt = f"""Gere duas versões de proposta freelance {lang_note} para a vaga abaixo.

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

VERSÃO 1 — proposal_direct:
- Máximo 2 parágrafos curtos
- Primeiro parágrafo: hook direto mostrando que entendeu o problema central
- Segundo parágrafo: como você resolve + CTA
- Tom: confiante, objetivo, sem rodeios

VERSÃO 2 — proposal_consultive:
- 3 parágrafos
- Primeiro: valida o desafio do cliente, mostra empatia e entendimento profundo
- Segundo: abordagem técnica proposta (sem revelar tudo), cite skills relevantes
- Terceiro: próximos passos concretos + pergunta engajante ao cliente
- Tom: consultivo, parceiro, não apenas executor

Ambas as versões:
- Personalizadas para os requisitos específicos desta vaga
- Sem inventar projetos ou clientes passados específicos
- Sugerir preço realista em USD

Retorne também:
- suggested_price: valor sugerido em USD (número) ou null
- estimated_hours: horas estimadas (inteiro) ou null
- proposal: igual ao proposal_direct (campo legado)"""

        return self.gemini.generate_structured(prompt, ProposalResult)
