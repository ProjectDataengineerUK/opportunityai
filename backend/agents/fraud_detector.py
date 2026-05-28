from pydantic import BaseModel
from services.gemini import GeminiClient


class FraudResult(BaseModel):
    risk_score: float  # 0–100
    flags: list[str]
    explanation: str


class FraudDetector:
    def __init__(self, gemini: GeminiClient):
        self.gemini = gemini

    def analyze(
        self,
        title: str,
        description: str,
        budget_min: float | None,
        budget_max: float | None,
    ) -> FraudResult:
        budget_str = "não informado"
        if budget_min is not None:
            budget_str = f"USD {budget_min}"
            if budget_max:
                budget_str += f" – {budget_max}"

        prompt = f"""Analise esta vaga freelance e identifique sinais de golpe ou fraude.

Título: {title}
Descrição: {description[:1000]}
Orçamento: {budget_str}

Sinais de alerta a verificar:
- Orçamento irreal (muito alto sem justificativa, ou pede pagamento adiantado)
- Pedido de "tarefa de teste gratuita" como parte da seleção
- Descrição extremamente vaga sem especificações técnicas
- Linguagem urgente e pressão para aceitar rápido
- Pedido de dados pessoais sensíveis ou acesso a contas
- Pagamento prometido fora da plataforma
- Promessas de renda passiva, ganhos fáceis ou bônus suspeitos
- Empresa ou cliente sem histórico verificável

Retorne:
- risk_score: 0 (seguro) a 100 (golpe evidente)
- flags: lista de sinais encontrados (lista vazia se seguro)
- explanation: explicação objetiva em português (1-2 linhas)"""

        return self.gemini.generate_structured(prompt, FraudResult)
