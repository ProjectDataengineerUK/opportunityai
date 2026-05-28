# BUILD REPORT — OpportunityAI MVP

**Data:** 2026-05-28
**Status:** COMPLETO
**Design:** DESIGN_OPPORTUNITYAI_MVP.md

---

## Resumo

41 arquivos criados. Todos os 31 itens do manifest implementados + `__init__.py` de módulos, `tests/`, `globals.css` e `layout.tsx`.

---

## Arquivos criados

### Fundação
| Arquivo | Status |
|---------|--------|
| `config.yaml` | ✅ Criado |
| `backend/models.py` | ✅ Criado |
| `backend/config.py` | ✅ Criado |
| `backend/services/gemini.py` | ✅ Criado |
| `backend/services/firestore.py` | ✅ Criado |

### Agentes
| Arquivo | Status |
|---------|--------|
| `backend/agents/sources/remoteok.py` | ✅ Criado |
| `backend/agents/sources/remotive.py` | ✅ Criado |
| `backend/agents/sources/freelancer.py` | ✅ Criado |
| `backend/agents/collector.py` | ✅ Criado |
| `backend/agents/classifier.py` | ✅ Criado |
| `backend/agents/evaluator.py` | ✅ Criado |

### API
| Arquivo | Status |
|---------|--------|
| `backend/routers/opportunities.py` | ✅ Criado |
| `backend/routers/collect.py` | ✅ Criado |
| `backend/main.py` | ✅ Criado |
| `backend/Dockerfile` | ✅ Criado |
| `backend/requirements.txt` | ✅ Criado |
| `backend/pyproject.toml` | ✅ Criado |

### Frontend
| Arquivo | Status |
|---------|--------|
| `frontend/lib/api.ts` | ✅ Criado |
| `frontend/components/ScoreBadge.tsx` | ✅ Criado |
| `frontend/components/FilterBar.tsx` | ✅ Criado |
| `frontend/components/CollectButton.tsx` | ✅ Criado |
| `frontend/components/OpportunityTable.tsx` | ✅ Criado |
| `frontend/app/layout.tsx` | ✅ Criado |
| `frontend/app/page.tsx` | ✅ Criado |
| `frontend/app/opportunities/[id]/page.tsx` | ✅ Criado |
| `frontend/Dockerfile` | ✅ Criado |
| `frontend/package.json` | ✅ Criado |

### Infra
| Arquivo | Status |
|---------|--------|
| `infra/terraform/variables.tf` | ✅ Criado |
| `infra/terraform/main.tf` | ✅ Criado |
| `infra/terraform/outputs.tf` | ✅ Criado |

### Extras
| Arquivo | Status |
|---------|--------|
| `.env.example` | ✅ Criado |
| `backend/tests/test_evaluator.py` | ✅ Criado (6 testes) |
| `backend/tests/test_classifier.py` | ✅ Criado (3 testes) |

---

## Decisões tomadas durante o build

1. **Deduplicação no Firestore** — `exists()` usa `where("external_id", "==", ...)` antes de salvar; evita vagas duplicadas entre coletas.

2. **Coleta paralela com `asyncio.gather`** — as 3 fontes são buscadas em paralelo; erros em uma fonte não bloqueiam as outras.

3. **Fallback de path do config.yaml** — `config.py` tenta `/app/config.yaml` (Cloud Run) e cai para `../config.yaml` (local dev).

4. **Strip de markdown no Gemini** — `gemini.py` remove blocos ` ```json ``` ` que o modelo pode incluir mesmo com instrução explícita.

5. **Singleton do FirestoreService** — instância reutilizada entre requests via variável global no router (evita reconexão por request).

6. **`asyncio.gather` com `return_exceptions=True`** — fontes que falham retornam a exceção sem derrubar a coleta inteira.

---

## Como rodar localmente

```bash
# 1. Copiar e preencher variáveis
cp .env.example .env
# editar .env com GEMINI_API_KEY e GCP_PROJECT_ID

# 2. Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --env-file ../.env

# 3. Frontend (em outro terminal)
cd frontend
npm install
npm run dev
```

## Como rodar os testes

```bash
cd backend
pip install pytest
pytest tests/ -v
```

## Como fazer deploy no GCP

```bash
# 1. Criar projeto GCP e habilitar billing
gcloud projects create SEU_PROJECT_ID
gcloud config set project SEU_PROJECT_ID

# 2. Build e push das imagens
gcloud builds submit --tag gcr.io/SEU_PROJECT_ID/opportunityai-backend ./backend
gcloud builds submit --tag gcr.io/SEU_PROJECT_ID/opportunityai-frontend ./frontend

# 3. Provisionar infra
cd infra/terraform
terraform init
terraform apply -var="project_id=SEU_PROJECT_ID"

# 4. Adicionar secrets
echo -n "SUA_GEMINI_KEY" | gcloud secrets versions add gemini-api-key --data-file=-
echo -n "SEU_FREELANCER_TOKEN" | gcloud secrets versions add freelancer-token --data-file=-
```

---

## Acceptance tests — status

| AT | Descrição | Status |
|----|-----------|--------|
| AT01 | Coletar Vagas → vagas aparecem em 30s | Implementado — requer infra real |
| AT02 | Filtro de idioma/orçamento na coleta | Implementado em `collector._filter()` |
| AT03 | Vaga Python/AI relevante → score >= 70 | Coberto por `test_evaluator.py` (mock) |
| AT04 | Vaga WordPress irrelevante → IGNORAR | Coberto por `test_evaluator.py` (mock) |
| AT05 | `terraform apply` sobe infra | Implementado — requer GCP real |
| AT06 | Detalhe da vaga exibe breakdown | Implementado em `opportunities/[id]/page.tsx` |

---

## Próximo passo

```bash
/ship .claude/sdd/features/DEFINE_OPPORTUNITYAI_MVP.md
```
