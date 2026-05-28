# DEFINE — OpportunityAI MVP

**Data:** 2026-05-28
**Status:** Aprovado — pronto para `/design`
**Clarity Score:** 14/15
**Input:** BRAINSTORM_OPPORTUNITYAI_MVP.md
**Próxima fase:** `/design .claude/sdd/features/DEFINE_OPPORTUNITYAI_MVP.md`

---

## Problema

Freelancers de IA, Dados e Programação perdem tempo peneirando manualmente dezenas de vagas ruins para encontrar oportunidades que realmente valem a pena. Não há forma rápida de saber se uma vaga é compatível com o perfil, se o orçamento é razoável ou se o cliente é confiável — tudo é julgamento manual e demorado.

---

## Usuário

**Persona:** Freelancer sênior de tecnologia (uso pessoal no MVP)

| Atributo | Valor |
|----------|-------|
| Skills principais | Python + Automação, IA/ML/LLMs, Data Engineering, Backend/APIs/Cloud |
| Valor mínimo por projeto | USD 200 |
| Idiomas aceitos | Português e Inglês |
| Plataformas alvo | RemoteOK, Remotive, Freelancer.com |
| Contexto | Usa o app sozinho para filtrar vagas antes de investir tempo em propostas |

---

## Objetivos

1. **Coletar** vagas automaticamente nas 3 plataformas configuradas, via disparo manual no dashboard
2. **Classificar** cada vaga por área técnica (IA, Dados, Python, Backend, Automação, Irrelevante)
3. **Avaliar** cada vaga com score 0–100 baseado em pesos configuráveis por critério
4. **Filtrar** vagas abaixo do valor mínimo ou em idiomas fora do perfil
5. **Exibir** ranking ordenado por score no dashboard com filtros e detalhe de vaga
6. **Operar** 100% na GCP, provisionado via Terraform

---

## Critérios de sucesso

| Critério | Como medir |
|----------|-----------|
| Coleta funciona | App busca e salva vagas reais das 3 APIs após clicar "Coletar" |
| Score é útil | As 5 vagas com maior score são realmente as mais relevantes para o perfil |
| Filtro funciona | Vagas abaixo de USD 200 e fora de PT/EN não aparecem no ranking |
| Dashboard responde | Página de ranking carrega em < 3s com até 200 vagas |
| Infra reproduzível | `terraform apply` sobe o ambiente do zero sem intervenção manual |

---

## Requisitos funcionais

### RF01 — Coleta de vagas
- O usuário clica em "Coletar Vagas" no dashboard
- O backend dispara coleta simultânea nas 3 APIs: RemoteOK, Remotive, Freelancer
- Vagas já coletadas (por URL ou ID externo) são ignoradas (deduplicação)
- Vagas em idiomas fora de PT/EN são descartadas na coleta
- Vagas com orçamento identificado abaixo de USD 200 são descartadas

### RF02 — Classificação por área
- Cada vaga recebe uma das categorias: `IA`, `Dados`, `Python`, `Backend`, `Automação`, `Cloud`, `Irrelevante`
- Classificação via Gemini 2.5 Flash com prompt estruturado
- Vagas classificadas como `Irrelevante` são salvas mas não exibidas por padrão

### RF03 — Score de compatibilidade
- Score de 0 a 100 calculado pelo Gemini 2.5 Flash
- Critérios e pesos definidos em `config.yaml` (editável sem redeploy):

```yaml
score_weights:
  skill_match: 0.35      # compatibilidade com perfil do usuário
  budget: 0.25           # orçamento vs. valor mínimo do usuário
  close_chance: 0.20     # histórico do cliente + clareza da vaga
  competition: 0.10      # número de propostas já enviadas
  clarity: 0.10          # vaga bem descrita e estruturada
```

- Decisão derivada do score:
  - ≥ 80: `APLICAR`
  - 50–79: `AVALIAR`
  - < 50: `IGNORAR`

### RF04 — Armazenamento
- Cada vaga salva no Firestore com campos: `id`, `source`, `title`, `description`, `budget`, `url`, `area`, `score`, `decision`, `collected_at`, `raw_data`
- Score e decisão podem ser recalculados sem re-coletar

### RF05 — Dashboard — Ranking
- Tabela ordenada por score (maior primeiro)
- Colunas: Score | Decisão | Título | Área | Plataforma | Orçamento | Data
- Filtros: por área, por decisão (APLICAR/AVALIAR/IGNORAR), por plataforma
- Botão "Coletar Vagas" dispara RF01
- Indicador de última coleta (data/hora)

### RF06 — Dashboard — Detalhe da vaga
- Resumo gerado pelo Gemini (3–5 linhas)
- Justificativa do score por critério
- Skills exigidas vs. skills do perfil
- Link para a vaga original
- Botão "Recalcular Score"

---

## Requisitos não-funcionais

| Requisito | Valor |
|-----------|-------|
| Plataforma | GCP 100% — Cloud Run + Firestore + Secret Manager |
| LLM principal | Gemini 2.5 Flash (scoring, classificação, resumo) |
| LLM avançado | Gemini 2.5 Pro (análises pesadas, opcional) |
| Infra como código | Terraform — `terraform apply` sobe tudo do zero |
| Autenticação | Nenhuma no MVP (uso pessoal) |
| Trigger de coleta | Manual via botão no dashboard (sem Cloud Scheduler) |
| Config de pesos | `config.yaml` editável sem redeploy |
| Latência dashboard | < 3s para carregar até 200 vagas |

---

## Fora do escopo (MVP)

| Feature | Motivo |
|---------|--------|
| Firebase Auth / login | Uso pessoal — sem necessidade |
| Cloud Scheduler (cron automático) | Usuário prefere disparo manual |
| Pub/Sub | Desnecessário sem coleta assíncrona complexa |
| Gerador de proposta | Fase 2 — primeiro valida o score |
| Anti-golpe com IA | MVP usa flags simples; IA vem na fase SaaS |
| LangGraph / CrewAI | Funções Python simples são suficientes no MVP |
| Upwork / Workana | APIs com restrições; fora do MVP |
| Cloud SQL PostgreSQL | Firestore é suficiente para MVP pessoal |
| Interface de config de pesos | Edita `config.yaml` diretamente |
| Notificações (e-mail / WhatsApp) | Fase 2 |

---

## Perfil de skills (usado pelo Avaliador)

```yaml
user_profile:
  skills:
    - Python
    - Automação
    - IA
    - Machine Learning
    - LLMs
    - Data Engineering
    - ETL
    - Backend
    - APIs REST
    - Cloud (GCP)
  min_budget_usd: 200
  languages:
    - pt
    - en
```

---

## Acceptance tests

### AT01 — Coleta funciona
```
DADO que o usuário clica em "Coletar Vagas"
QUANDO o backend processa a requisição
ENTÃO novas vagas aparecem no ranking dentro de 30s
E vagas já existentes não são duplicadas
```

### AT02 — Filtro de idioma e orçamento
```
DADO que existem vagas em espanhol e vagas com orçamento USD 50
QUANDO a coleta é processada
ENTÃO essas vagas não aparecem no ranking
```

### AT03 — Score útil
```
DADO uma vaga de "Python automation specialist" com orçamento USD 500
QUANDO o avaliador processa
ENTÃO o score é >= 70 e a decisão é APLICAR ou AVALIAR
```

### AT04 — Score inútil descartado
```
DADO uma vaga de "WordPress designer" com orçamento USD 100
QUANDO o avaliador processa
ENTÃO o score é < 50 e a decisão é IGNORAR
```

### AT05 — Infra reproduzível
```
DADO um projeto GCP vazio com as APIs habilitadas
QUANDO `terraform apply` é executado
ENTÃO Cloud Run, Firestore e Secret Manager estão provisionados
E o dashboard está acessível via URL do Cloud Run
```

### AT06 — Detalhe da vaga
```
DADO que o usuário clica em uma vaga no ranking
QUANDO a página de detalhe abre
ENTÃO exibe: resumo Gemini, score por critério, skills match e link original
```

---

## Arquitetura de alto nível

```
[Dashboard Next.js — Cloud Run ou Firebase Hosting]
    │
    ├── GET /api/opportunities  → lista vagas do Firestore
    ├── GET /api/opportunities/{id}  → detalhe de vaga
    └── POST /api/collect  → dispara coleta
          │
          ▼
[Backend FastAPI — Cloud Run]
    │
    ├── collector.py  → RemoteOK + Remotive + Freelancer API
    ├── classifier.py  → Gemini 2.5 Flash
    ├── evaluator.py   → Gemini 2.5 Flash + config.yaml
    └── firestore.py   → CRUD no Firestore
          │
          ▼
[Firestore] ← [Secret Manager]  ← Chaves: Gemini API, Freelancer OAuth
```

---

## Dependências externas

| Dependência | Tipo | Notas |
|-------------|------|-------|
| RemoteOK API | HTTP pública | `remoteok.com/api` — gratuita, sem auth |
| Remotive API | HTTP pública | `remotive.com/api/remote-jobs` — gratuita |
| Freelancer API | OAuth 2.0 | Requer app em developers.freelancer.com |
| Gemini 2.5 Flash | Google AI API | Chave via Secret Manager |
| GCP Project | Infra | Projeto novo a criar |

---

## Marcos do MVP

| Marco | Entregável |
|-------|-----------|
| M1 — Infra | Terraform sobe Cloud Run + Firestore + Secret Manager |
| M2 — Coleta | RemoteOK + Remotive coletando vagas reais |
| M3 — Dashboard | Ranking exibindo vagas com score mockado |
| M4 — Avaliador | Gemini 2.5 Flash calculando score real |
| M5 — Freelancer | Integração OAuth com Freelancer API |
| M6 — Completo | AT01–AT06 todos passando |
