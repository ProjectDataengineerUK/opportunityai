# DESIGN — OpportunityAI MVP

**Data:** 2026-05-28
**Status:** Aprovado — pronto para `/build`
**Input:** DEFINE_OPPORTUNITYAI_MVP.md
**Próxima fase:** `/build .claude/sdd/features/DESIGN_OPPORTUNITYAI_MVP.md`

---

## Diagrama da arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    GCP Project                               │
│                                                             │
│  ┌──────────────────────┐     ┌─────────────────────────┐  │
│  │  Frontend (Next.js)  │────▶│  Backend (FastAPI)      │  │
│  │  Cloud Run           │     │  Cloud Run              │  │
│  │                      │     │                         │  │
│  │  /           Ranking │     │  POST /api/collect      │  │
│  │  /[id]       Detalhe │     │  GET  /api/opportunities│  │
│  │  [Coletar Vagas btn] │     │  GET  /api/opportunities│  │
│  └──────────────────────┘     │       /{id}             │  │
│                               └────────────┬────────────┘  │
│                                            │               │
│                               ┌────────────▼────────────┐  │
│                               │  Agents (Python)         │  │
│                               │                         │  │
│                               │  collector.py           │  │
│                               │  ├── remoteok.py        │  │
│                               │  ├── remotive.py        │  │
│                               │  └── freelancer.py      │  │
│                               │  classifier.py          │  │
│                               │  evaluator.py           │  │
│                               └────────┬────────────────┘  │
│                                        │                   │
│              ┌─────────────────────────▼──────────────┐    │
│              │  Firestore                              │    │
│              │  Collection: opportunities              │    │
│              └─────────────────────────────────────────┘    │
│                                                             │
│  ┌──────────────────────┐     ┌─────────────────────────┐  │
│  │  Secret Manager      │     │  Gemini 2.5 Flash API   │  │
│  │  - GEMINI_API_KEY    │     │  (external)             │  │
│  │  - FREELANCER_TOKEN  │     └─────────────────────────┘  │
│  └──────────────────────┘                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Fluxo de dados

```
1. Usuário clica "Coletar Vagas" no dashboard
2. Frontend → POST /api/collect
3. Backend dispara collector.py
4. collector.py busca em paralelo:
   ├── remoteok.py  → GET remoteok.com/api?tags=python,ai,data
   ├── remotive.py  → GET remotive.com/api/remote-jobs?category=software-dev
   └── freelancer.py → GET api.freelancer.com/projects/0.1/projects/...
5. Cada vaga passa por deduplicação (external_id no Firestore)
6. Vagas novas → classifier.py (Gemini 2.5 Flash)
   └── retorna: area (IA | Dados | Python | Backend | Automação | Cloud | Irrelevante)
7. Vagas classificadas → evaluator.py (Gemini 2.5 Flash + config.yaml)
   └── retorna: score (0-100), score_breakdown, decision
8. Resultado salvo no Firestore
9. Frontend re-fetch GET /api/opportunities → exibe ranking atualizado
```

---

## Componentes

| Componente | Tecnologia | Responsabilidade |
|-----------|-----------|-----------------|
| Frontend | Next.js 14 + Tailwind + shadcn/ui | Ranking, filtros, detalhe de vaga |
| Backend | Python 3.11 + FastAPI | API REST, orquestração dos agentes |
| Collector | Python | Busca vagas nas APIs externas |
| Classifier | Python + Gemini 2.5 Flash | Classifica área da vaga |
| Evaluator | Python + Gemini 2.5 Flash | Calcula score e decisão |
| Firestore | GCP Firestore | Armazenamento das vagas |
| Secret Manager | GCP Secret Manager | Chaves de API |
| Terraform | HashiCorp Terraform | Provisionamento da infra GCP |

---

## Decisões de arquitetura (ADRs)

### ADR-01: Firestore em vez de Cloud SQL

| | |
|-|-|
| **Status** | Aceito |
| **Data** | 2026-05-28 |

**Contexto:** Precisamos de banco para armazenar vagas com campos variáveis (cada API retorna estrutura diferente).

**Escolha:** Firestore (documento NoSQL)

**Rationale:** Schema flexível para `raw_data` de múltiplas APIs; sem necessidade de migrations; gratuito até 1GB/50k leituras por dia; suficiente para MVP pessoal.

**Alternativas rejeitadas:**
- Cloud SQL PostgreSQL — overhead de provisionamento, custo mínimo ~$7/mês, schema rígido
- SQLite local — não funciona em Cloud Run stateless

**Consequências:** Sem JOINs; queries complexas são mais verbosas. Aceitável no MVP.

---

### ADR-02: Coleta síncrona em vez de Pub/Sub

| | |
|-|-|
| **Status** | Aceito |
| **Data** | 2026-05-28 |

**Contexto:** MVP com trigger manual (botão no dashboard).

**Escolha:** Coleta síncrona — POST /api/collect bloqueia até terminar.

**Rationale:** Sem Pub/Sub, sem Cloud Tasks, sem complexidade de mensageria. Volume é baixo (dezenas de vagas por coleta). Usuário aguarda ~10–20s após clicar.

**Alternativas rejeitadas:**
- Pub/Sub + Cloud Run — arquitetura correta para produção, mas desnecessária para MVP pessoal
- Background thread no FastAPI — complica o container sem ganho real no MVP

**Consequências:** Request pode demorar 10–30s. Frontend mostra spinner. Aceitável.

---

### ADR-03: Gemini 2.5 Flash para todas as tarefas de IA

| | |
|-|-|
| **Status** | Aceito |
| **Data** | 2026-05-28 |

**Contexto:** Precisamos de LLM para classificação, scoring e resumo de vagas.

**Escolha:** Gemini 2.5 Flash como modelo padrão; 2.5 Pro disponível via config.

**Rationale:** Flash é 10x mais barato que Pro; latência menor; suficiente para tarefas de classificação e scoring estruturado. Pro fica reservado para análises pesadas futuras.

**Alternativas rejeitadas:**
- OpenAI GPT-4o — sem vantagem técnica para este caso; custo maior; não nativo GCP
- Modelo local (Ollama) — não funciona no Cloud Run sem GPU

**Consequências:** Custo por coleta de 50 vagas estimado em < USD 0.10.

---

### ADR-04: config.yaml no container em vez de Firestore

| | |
|-|-|
| **Status** | Aceito |
| **Data** | 2026-05-28 |

**Contexto:** Pesos do score precisam ser configuráveis sem redeploy.

**Escolha:** `config.yaml` montado como volume no Cloud Run via Secret Manager ou baked no container.

**Rationale:** Para MVP pessoal, editar e redeploy é aceitável (< 2min com Cloud Run). Alternativa de UI de config é prematura.

**Alternativas rejeitadas:**
- Firestore para config — overkill para um único arquivo YAML
- Variáveis de ambiente — difícil para estrutura hierárquica de pesos

---

### ADR-05: Frontend separado do Backend

| | |
|-|-|
| **Status** | Aceito |
| **Data** | 2026-05-28 |

**Contexto:** Next.js + FastAPI — dois serviços distintos.

**Escolha:** Dois Cloud Run services; frontend consome backend via HTTP.

**Rationale:** Permite deploy independente; padrão moderno; facilita evolução para SaaS.

**Consequências:** CORS necessário no backend. Backend URL configurada como env var no frontend.

---

## Schema do Firestore

### Collection: `opportunities`

```typescript
interface Opportunity {
  id: string;                    // Firestore auto-ID
  external_id: string;           // "{source}:{id_original}" — para dedup
  source: "remoteok" | "remotive" | "freelancer";
  title: string;
  description: string;
  budget_min: number | null;
  budget_max: number | null;
  budget_currency: string | null; // "USD" | "BRL" | null
  url: string;
  area: "IA" | "Dados" | "Python" | "Backend" | "Automação" | "Cloud" | "Irrelevante";
  score: number;                 // 0-100
  score_breakdown: {
    skill_match: number;         // 0-100
    budget: number;              // 0-100
    close_chance: number;        // 0-100
    competition: number;         // 0-100
    clarity: number;             // 0-100
  };
  decision: "APLICAR" | "AVALIAR" | "IGNORAR";
  summary: string;               // resumo gerado pelo Gemini
  language: string;              // "pt" | "en" | outro
  collected_at: Timestamp;
  raw_data: Record<string, unknown>;
}
```

**Índices necessários:**
- `score` DESC (ranking principal)
- `area` ASC + `score` DESC (filtro por área)
- `decision` ASC + `score` DESC (filtro por decisão)
- `source` ASC + `score` DESC (filtro por plataforma)
- `external_id` ASC (deduplicação — único)

---

## Manifest de arquivos

| # | Arquivo | Ação | Propósito | Deps |
|---|---------|------|-----------|------|
| 1 | `config.yaml` | Criar | Pesos do score + perfil do usuário | — |
| 2 | `backend/requirements.txt` | Criar | Dependências Python | — |
| 3 | `backend/pyproject.toml` | Criar | Config do projeto Python | — |
| 4 | `backend/models.py` | Criar | Pydantic models (Opportunity, ScoreBreakdown) | — |
| 5 | `backend/config.py` | Criar | Loader de config.yaml + env vars | 1 |
| 6 | `backend/services/gemini.py` | Criar | Wrapper Gemini API client | 2 |
| 7 | `backend/services/firestore.py` | Criar | CRUD Firestore | 2 |
| 8 | `backend/agents/sources/remoteok.py` | Criar | Cliente RemoteOK API | 2 |
| 9 | `backend/agents/sources/remotive.py` | Criar | Cliente Remotive API | 2 |
| 10 | `backend/agents/sources/freelancer.py` | Criar | Cliente Freelancer OAuth | 2 |
| 11 | `backend/agents/collector.py` | Criar | Orquestra coleta das 3 fontes | 8, 9, 10 |
| 12 | `backend/agents/classifier.py` | Criar | Classificação de área via Gemini | 6 |
| 13 | `backend/agents/evaluator.py` | Criar | Score via Gemini + config.yaml | 5, 6 |
| 14 | `backend/routers/opportunities.py` | Criar | GET /api/opportunities + /{id} | 7, 4 |
| 15 | `backend/routers/collect.py` | Criar | POST /api/collect | 11, 12, 13, 7 |
| 16 | `backend/main.py` | Criar | FastAPI app + CORS + routers | 14, 15 |
| 17 | `backend/Dockerfile` | Criar | Container Python 3.11 slim | 2 |
| 18 | `frontend/package.json` | Criar | Dependências Next.js | — |
| 19 | `frontend/lib/api.ts` | Criar | API client (fetch wrapper) | — |
| 20 | `frontend/components/ScoreBadge.tsx` | Criar | Badge score + decisão colorida | — |
| 21 | `frontend/components/FilterBar.tsx` | Criar | Filtros área/decisão/plataforma | — |
| 22 | `frontend/components/CollectButton.tsx` | Criar | Botão + spinner de coleta | 19 |
| 23 | `frontend/components/OpportunityTable.tsx` | Criar | Tabela ranking com ordenação | 20, 21 |
| 24 | `frontend/app/page.tsx` | Criar | Página principal (dashboard) | 22, 23 |
| 25 | `frontend/app/opportunities/[id]/page.tsx` | Criar | Página detalhe da vaga | 19, 20 |
| 26 | `frontend/app/layout.tsx` | Criar | Layout base Next.js | — |
| 27 | `frontend/Dockerfile` | Criar | Container Node.js | 18 |
| 28 | `infra/terraform/variables.tf` | Criar | Variáveis (project_id, region) | — |
| 29 | `infra/terraform/main.tf` | Criar | Provider + Cloud Run + Firestore + Secret Manager | 28 |
| 30 | `infra/terraform/outputs.tf` | Criar | URLs dos Cloud Run services | 29 |
| 31 | `.env.example` | Criar | Template de variáveis de ambiente | — |

---

## Padrões de código

### config.yaml

```yaml
# Perfil do usuário
user_profile:
  skills:
    - Python
    - Automação
    - IA
    - Machine Learning
    - LLMs
    - Data Engineering
    - Backend
    - APIs REST
    - Cloud GCP
  min_budget_usd: 200
  languages:
    - pt
    - en

# Pesos do score (devem somar 1.0)
score_weights:
  skill_match: 0.35
  budget: 0.25
  close_chance: 0.20
  competition: 0.10
  clarity: 0.10

# Decisão por faixa de score
decision_thresholds:
  aplicar: 80
  avaliar: 50
  # abaixo de 50 → IGNORAR

# Modelos Gemini
gemini:
  default_model: gemini-2.5-flash
  advanced_model: gemini-2.5-pro

# Fontes habilitadas
sources:
  remoteok: true
  remotive: true
  freelancer: true
```

---

### backend/models.py

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Literal

class ScoreBreakdown(BaseModel):
    skill_match: float
    budget: float
    close_chance: float
    competition: float
    clarity: float

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
    language: str
    collected_at: datetime
```

---

### backend/services/gemini.py — saída estruturada

```python
import google.generativeai as genai
import json
from typing import TypeVar, Type
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class GeminiClient:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

    def generate_structured(self, prompt: str, schema: Type[T]) -> T:
        schema_json = schema.model_json_schema()
        full_prompt = f"{prompt}\n\nResponda APENAS com JSON válido seguindo este schema:\n{json.dumps(schema_json, indent=2)}"
        response = self.model.generate_content(full_prompt)
        return schema.model_validate_json(response.text)
```

---

### backend/agents/classifier.py

```python
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
        prompt = f"""Classifique esta vaga freelance em uma das áreas técnicas.

Título: {title}
Descrição: {description[:800]}

Áreas disponíveis:
- IA: machine learning, LLMs, deep learning, NLP, visão computacional
- Dados: data engineering, ETL, pipelines, analytics, BigQuery, dbt
- Python: automação, scripting, APIs, scraping
- Backend: APIs REST, microsserviços, servidores
- Automação: RPA, workflows, bots, integração de sistemas
- Cloud: DevOps, infraestrutura, Kubernetes, Terraform
- Irrelevante: design, WordPress, mobile sem relação com as áreas acima"""

        result = self.gemini.generate_structured(prompt, ClassificationResult)
        return result.area
```

---

### backend/agents/evaluator.py

```python
from pydantic import BaseModel
from services.gemini import GeminiClient
from config import AppConfig

class EvaluationResult(BaseModel):
    score: float                  # 0-100
    skill_match: float            # 0-100
    budget_score: float           # 0-100
    close_chance: float           # 0-100
    competition: float            # 0-100
    clarity: float                # 0-100
    summary: str                  # 3-5 linhas
    skills_required: list[str]

class Evaluator:
    def __init__(self, gemini: GeminiClient, config: AppConfig):
        self.gemini = gemini
        self.config = config

    def evaluate(self, title: str, description: str, budget_min: float | None) -> EvaluationResult:
        profile = self.config.user_profile
        weights = self.config.score_weights

        prompt = f"""Avalie esta vaga freelance para o perfil abaixo.

PERFIL DO FREELANCER:
- Skills: {', '.join(profile['skills'])}
- Valor mínimo: USD {profile['min_budget_usd']}
- Idiomas: {', '.join(profile['languages'])}

VAGA:
Título: {title}
Descrição: {description[:1200]}
Orçamento mínimo: {f'USD {budget_min}' if budget_min else 'não informado'}

Avalie cada critério de 0 a 100:
- skill_match: compatibilidade das skills exigidas com o perfil
- budget_score: orçamento vs valor mínimo do freelancer
- close_chance: histórico do cliente + clareza + competição estimada
- competition: quanto menor a concorrência, maior a nota
- clarity: quão bem descrita e estruturada é a vaga

Gere também um resumo de 3-5 linhas em português e a lista de skills exigidas."""

        result = self.gemini.generate_structured(prompt, EvaluationResult)

        # Score ponderado
        w = weights
        result.score = (
            result.skill_match * w['skill_match'] +
            result.budget_score * w['budget'] +
            result.close_chance * w['close_chance'] +
            result.competition * w['competition'] +
            result.clarity * w['clarity']
        )

        return result
```

---

### backend/services/firestore.py — deduplicação

```python
from google.cloud import firestore
from models import Opportunity
from datetime import datetime

class FirestoreService:
    def __init__(self):
        self.db = firestore.Client()
        self.collection = self.db.collection("opportunities")

    def exists(self, external_id: str) -> bool:
        docs = self.collection.where("external_id", "==", external_id).limit(1).get()
        return len(docs) > 0

    def save(self, opportunity: Opportunity) -> str:
        doc_ref = self.collection.document()
        data = opportunity.model_dump()
        data["collected_at"] = datetime.utcnow()
        doc_ref.set(data)
        return doc_ref.id

    def list_opportunities(
        self,
        area: str | None = None,
        decision: str | None = None,
        source: str | None = None,
        limit: int = 200,
    ) -> list[dict]:
        query = self.collection.order_by("score", direction=firestore.Query.DESCENDING)
        if area:
            query = query.where("area", "==", area)
        if decision:
            query = query.where("decision", "==", decision)
        if source:
            query = query.where("source", "==", source)
        return [{"id": doc.id, **doc.to_dict()} for doc in query.limit(limit).get()]
```

---

### backend/routers/collect.py

```python
from fastapi import APIRouter, BackgroundTasks, HTTPException
from agents.collector import Collector
from agents.classifier import Classifier
from agents.evaluator import Evaluator
from services.firestore import FirestoreService
from services.gemini import GeminiClient
from config import get_config

router = APIRouter()

@router.post("/api/collect")
async def collect_opportunities():
    config = get_config()
    gemini = GeminiClient(api_key=config.gemini_api_key, model=config.gemini.default_model)
    firestore_svc = FirestoreService()
    classifier = Classifier(gemini)
    evaluator = Evaluator(gemini, config)
    collector = Collector(config)

    raw_jobs = await collector.collect_all()
    saved = 0

    for job in raw_jobs:
        if firestore_svc.exists(job.external_id):
            continue
        area = classifier.classify(job.title, job.description)
        if area == "Irrelevante":
            continue
        eval_result = evaluator.evaluate(job.title, job.description, job.budget_min)
        opportunity = build_opportunity(job, area, eval_result, config)
        firestore_svc.save(opportunity)
        saved += 1

    return {"collected": len(raw_jobs), "saved": saved}
```

---

### frontend/lib/api.ts

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL;

export interface Opportunity {
  id: string;
  source: "remoteok" | "remotive" | "freelancer";
  title: string;
  area: string;
  score: number;
  decision: "APLICAR" | "AVALIAR" | "IGNORAR";
  budget_min: number | null;
  budget_max: number | null;
  budget_currency: string | null;
  url: string;
  summary: string;
  collected_at: string;
}

export async function listOpportunities(params?: {
  area?: string;
  decision?: string;
  source?: string;
}): Promise<Opportunity[]> {
  const qs = new URLSearchParams(params as Record<string, string>).toString();
  const res = await fetch(`${API_URL}/api/opportunities${qs ? `?${qs}` : ""}`);
  if (!res.ok) throw new Error("Failed to fetch opportunities");
  return res.json();
}

export async function collectOpportunities(): Promise<{ collected: number; saved: number }> {
  const res = await fetch(`${API_URL}/api/collect`, { method: "POST" });
  if (!res.ok) throw new Error("Collection failed");
  return res.json();
}
```

---

### infra/terraform/main.tf (esqueleto)

```hcl
terraform {
  required_providers {
    google = { source = "hashicorp/google", version = "~> 5.0" }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Firestore
resource "google_firestore_database" "default" {
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
}

# Secret: Gemini API Key
resource "google_secret_manager_secret" "gemini_api_key" {
  secret_id = "gemini-api-key"
  replication { auto {} }
}

# Secret: Freelancer Token
resource "google_secret_manager_secret" "freelancer_token" {
  secret_id = "freelancer-token"
  replication { auto {} }
}

# Cloud Run — Backend
resource "google_cloud_run_v2_service" "backend" {
  name     = "opportunityai-backend"
  location = var.region

  template {
    containers {
      image = "gcr.io/${var.project_id}/opportunityai-backend:latest"
      env {
        name  = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.gemini_api_key.secret_id
            version = "latest"
          }
        }
      }
    }
  }
}

# Cloud Run — Frontend
resource "google_cloud_run_v2_service" "frontend" {
  name     = "opportunityai-frontend"
  location = var.region

  template {
    containers {
      image = "gcr.io/${var.project_id}/opportunityai-frontend:latest"
      env {
        name  = "NEXT_PUBLIC_API_URL"
        value = google_cloud_run_v2_service.backend.uri
      }
    }
  }
}
```

---

## Estratégia de testes

| Tipo | Escopo | Ferramenta | Quando |
|------|--------|-----------|--------|
| Unit | classifier.py, evaluator.py (com Gemini mockado) | pytest | A cada mudança nos agentes |
| Unit | firestore.py (com emulador Firestore) | pytest + Firestore emulator | A cada mudança no storage |
| Integration | POST /api/collect → Firestore (APIs externas mockadas) | pytest + httpx | Antes de cada deploy |
| E2E | Clicar "Coletar" no dashboard → vagas aparecem | Manual (Playwright fase 2) | Validação do AT01 |

### Teste unitário mínimo — evaluator

```python
# tests/test_evaluator.py
from unittest.mock import MagicMock
from agents.evaluator import Evaluator, EvaluationResult

def test_evaluate_returns_score_in_range():
    gemini_mock = MagicMock()
    gemini_mock.generate_structured.return_value = EvaluationResult(
        score=0, skill_match=90, budget_score=80, close_chance=70,
        competition=60, clarity=85,
        summary="Vaga de Python com bom orçamento.",
        skills_required=["Python", "FastAPI"]
    )
    config = MagicMock()
    config.score_weights = dict(skill_match=0.35, budget=0.25, close_chance=0.20, competition=0.10, clarity=0.10)
    config.user_profile = {"skills": ["Python"], "min_budget_usd": 200, "languages": ["pt", "en"]}

    evaluator = Evaluator(gemini_mock, config)
    result = evaluator.evaluate("Python Dev", "Need Python expert", 500)

    assert 0 <= result.score <= 100
```

---

## Variáveis de ambiente

### Backend (Cloud Run)
| Variável | Fonte | Exemplo |
|----------|-------|---------|
| `GEMINI_API_KEY` | Secret Manager | `AIza...` |
| `FREELANCER_CLIENT_ID` | Secret Manager | `123456` |
| `FREELANCER_TOKEN` | Secret Manager | `Bearer xxx` |
| `GCP_PROJECT_ID` | Env var Cloud Run | `opportunityai-prod` |

### Frontend (Cloud Run)
| Variável | Fonte | Exemplo |
|----------|-------|---------|
| `NEXT_PUBLIC_API_URL` | Terraform output | `https://opportunityai-backend-xxx.run.app` |

---

## Ordem de build (dependências)

```
Fase 1 — Fundação
  1. config.yaml
  2. backend/models.py
  3. backend/config.py
  4. backend/services/gemini.py
  5. backend/services/firestore.py

Fase 2 — Agentes
  6. backend/agents/sources/remoteok.py
  7. backend/agents/sources/remotive.py
  8. backend/agents/sources/freelancer.py
  9. backend/agents/collector.py
  10. backend/agents/classifier.py
  11. backend/agents/evaluator.py

Fase 3 — API
  12. backend/routers/opportunities.py
  13. backend/routers/collect.py
  14. backend/main.py
  15. backend/Dockerfile
  16. backend/requirements.txt

Fase 4 — Frontend
  17. frontend/lib/api.ts
  18. frontend/components/* (ScoreBadge, FilterBar, CollectButton, OpportunityTable)
  19. frontend/app/page.tsx
  20. frontend/app/opportunities/[id]/page.tsx
  21. frontend/Dockerfile

Fase 5 — Infra
  22. infra/terraform/variables.tf
  23. infra/terraform/main.tf
  24. infra/terraform/outputs.tf
```
