from pydantic import BaseModel
from typing import Literal
from services.gemini import GeminiClient

Area = Literal["IA", "Dados", "Python", "Backend", "Automação", "Cloud", "Irrelevante"]


class ClassificationResult(BaseModel):
    area: Area
    reason: str


class Classifier:
    def __init__(self, gemini: GeminiClient):
        self.gemini = gemini

    def classify(self, title: str, description: str) -> Area:
        prompt = f"""Classifique esta vaga freelance em exatamente uma das áreas técnicas abaixo.

Título: {title}
Descrição: {description[:800]}

Áreas:
- IA: machine learning, LLMs, deep learning, NLP, visão computacional, Gemini, OpenAI
- Dados: data engineering, ETL, pipelines, analytics, BigQuery, dbt, Spark, SQL avançado
- Python: automação, scripting, web scraping, bots, processamento de arquivos
- Backend: APIs REST, FastAPI, Django, Flask, microsserviços, servidores
- Automação: RPA, workflows, Zapier-like, integração de sistemas, n8n
- Cloud: GCP, AWS, Azure, DevOps, Kubernetes, Terraform, infraestrutura
- Irrelevante: design gráfico, WordPress, mobile nativo, jogos, conteúdo sem relação técnica"""

        result = self.gemini.generate_structured(prompt, ClassificationResult)
        return result.area
