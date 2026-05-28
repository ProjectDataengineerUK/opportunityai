# OpportunityAI

> App inteligente de seleção de oportunidades freelance em IA, Dados e Programação. Coleta vagas em múltiplas plataformas (Upwork, Freelancer, Workana, RemoteOK, Remotive), aplica pontuação automática com IA e multiagentes, detecta golpes e gera propostas personalizadas. Arquitetura cloud-native na GCP.

---

## Stack

- **Linguagem:** Python 3.11+
- **Backend:** FastAPI
- **Frontend:** Next.js + Tailwind CSS + shadcn/ui
- **Banco de dados:** Firestore (MVP) → Cloud SQL PostgreSQL (produção)
- **IA/LLM:** Gemini API / Vertex AI
- **Multiagentes:** LangGraph ou CrewAI
- **Mensageria:** GCP Pub/Sub
- **Agendamento:** Cloud Scheduler
- **Deploy:** Cloud Run (backend + agentes)
- **Auth:** Firebase Auth
- **Hosting:** Firebase Hosting
- **Infra:** Terraform
- **Gráficos:** Recharts

## Estrutura

```
OpportunityAI/
├── backend/
│   ├── agents/
│   │   ├── collector.py        # Coleta vagas nas APIs externas
│   │   ├── classifier.py       # Classifica área da vaga (IA, Dados, etc.)
│   │   ├── evaluator.py        # Score 0-100 por compatibilidade/orçamento
│   │   ├── fraud_detector.py   # Detecta sinais de golpe
│   │   └── proposal_generator.py  # Gera proposta personalizada
│   ├── services/
│   │   ├── pubsub.py
│   │   ├── firestore.py
│   │   └── gemini.py
│   ├── api/
│   ├── main.py
│   └── Dockerfile
├── frontend/
│   └── nextjs-app/
├── infra/
│   └── terraform/
└── CONTEXT.md
```

## Arquivos-chave

| Arquivo | Função |
|---------|--------|
| `CONTEXT.md` | Histórico do planejamento inicial (ChatGPT) — contexto completo do projeto |
| `backend/main.py` | Entry point FastAPI |
| `backend/agents/evaluator.py` | Score de oportunidades com Gemini |
| `backend/agents/proposal_generator.py` | Gerador de propostas com LLM |
| `backend/services/gemini.py` | Integração com Gemini API |
| `infra/terraform/` | Infraestrutura GCP (Cloud Run, Pub/Sub, Firestore) |

## Convenções

- **Linter:** não configurado
- **Formatter:** não configurado
- **Testes:** não configurado

## Como rodar

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend/nextjs-app
npm install
npm run dev
```

---

## Agentes recomendados (agentcode)

| Agente | Quando usar |
|--------|-------------|
| `@brainstorm-agent` | Explorar features, comparar abordagens, definir escopo |
| `@the-planner` | Planejar arquitetura, roadmap, decisões técnicas |
| `@design-agent` | Criar especificação técnica e arquitetura detalhada |
| `@genai-architect` | Desenhar o sistema multiagente com LangGraph/CrewAI |
| `@ai-prompt-specialist` | Otimizar prompts para Gemini (scoring, proposta, classificação) |
| `@gcp-data-architect` | Arquitetura GCP: Cloud Run, Pub/Sub, Firestore, Vertex AI |
| `@ai-data-engineer-gcp` | Pipelines de coleta e processamento de vagas no GCP |
| `@python-developer` | Escrever e refatorar código Python dos agentes |
| `@python-reviewer` | Revisar código Python — FastAPI, agentes, serviços |
| `@security-reviewer` | Revisar autenticação, Firebase Auth, APIs externas |
| `@code-reviewer` | Revisão geral de qualidade após qualquer mudança de código |

## Comandos úteis

| Comando | Quando usar |
|---------|-------------|
| `/brainstorm` | Explorar features novas ou abordagens alternativas |
| `/define` | Capturar requisitos formais de uma feature |
| `/design` | Criar especificação técnica detalhada |
| `/workflow` | Implementar feature com LLM/multiagentes |
| `/pipeline` | Desenhar pipeline de coleta de vagas no GCP |
| `/status` | Ver estado atual do projeto |
| `/preflight` | Validar projeto antes de avançar |

---

_Gerado por `/start` em 2026-05-28._
