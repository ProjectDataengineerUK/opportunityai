# DEFINE — OpportunityAI V2 (pós-MVP)

**Data:** 2026-05-31
**Status:** Engenharia reversa — documenta o que JÁ foi construído além do MVP
**Input:** DEFINE_OPPORTUNITYAI_MVP.md + varredura profunda do código (2026-05-31)
**Baseline:** 33 testes passando · CI/CD completo (WIF + Terraform + Cloud Run)

> ⚠️ Este documento foi gerado por varredura do código real, não por planejamento prévio.
> Várias features marcadas como "Fora do escopo (MVP)" no DEFINE original já estão implementadas.
> Serve para realinhar o SDD com a realidade antes do próximo ciclo.

---

## Como o escopo mudou desde o MVP

| Feature | DEFINE MVP | Realidade V2 |
|---------|-----------|--------------|
| Fontes de vagas | RemoteOK, Remotive, Freelancer | **+ Upwork (GraphQL/OAuth2), + Workana (scraping XHR)** |
| Detecção de fraude | "flags simples, IA na fase SaaS" | **`fraud_detector.py` com Gemini — descarta vagas com risk > 80** |
| Gerador de proposta | "Fase 2" | **`proposal_generator.py` — proposta DUPLA (direta + consultiva) + preço/horas sugeridos** |
| Análise do cliente | não previsto | **`client_analyzer.py` — score do cliente, hire rate, payment verified, total spent, urgência** |
| Notificações | "Fase 2 (e-mail/WhatsApp)" | **`telegram.py` — push das top 5 vagas APLICAR via bot** |
| Aprendizado/outcomes | não previsto | **Tracking de desfecho (ganhou/perdeu/sem_resposta) + `/stats/win-rate`** |
| Recalcular score | botão no detalhe | **endpoint `POST /opportunities/{id}/recalculate`** ✅ |
| CI/CD | não previsto no MVP | **GitHub Actions: test → terraform → build/deploy, WIF, sem segredos no CI** |

---

## Requisitos funcionais ADICIONAIS (já implementados)

### RF07 — Detecção de fraude com IA
- `FraudDetector` (Gemini Flash) analisa título/descrição/orçamento e retorna `risk_score` (0–100), `flags[]`, `explanation`
- Na coleta, vagas com `risk_score > 80` são descartadas e contadas em `skipped_fraud`
- Sinais verificados: orçamento irreal, teste grátis, descrição vaga, pressão/urgência, pedido de dados sensíveis, pagamento fora da plataforma, renda passiva, cliente sem histórico
- `fraud_risk` e `fraud_flags` ficam persistidos na Opportunity para exibição

### RF08 — Análise do cliente e urgência
- `ClientAnalyzer` (heurístico, sem LLM) extrai sinais do `raw_data` por fonte:
  - **Freelancer:** hire_rate, earnings_score, payment_verified, bid_count, time_submitted
  - **Upwork:** totalSpent, verificationStatus, totalApplicants, createdDateTime
  - **Workana:** hasVerifiedPaymentMethod, totalBids
  - **RemoteOK/Remotive:** apenas data de publicação
- `client_score` (0–100) derivado de payment_verified (+20), hire_rate (até +20/−15) e total_spent (até +15/−10), base neutra 50
- `urgency` ∈ {quente, normal, frio} a partir de idade do post + nº de propostas:
  - **quente:** < 24h e < 10 propostas
  - **frio:** > 72h ou > 25 propostas
  - **normal:** caso contrário

### RF09 — Geração de proposta dupla
- `ProposalGenerator` (Gemini **Pro**) gera duas versões via `POST /opportunities/{id}/proposal`:
  - **proposal_direct:** 2 parágrafos, hook + solução + CTA, tom objetivo
  - **proposal_consultive:** 3 parágrafos, valida desafio → abordagem técnica → próximos passos
- Retorna também `suggested_price` (USD) e `estimated_hours`
- Campo legado `proposal` = cópia da direta
- Restrição de prompt: não inventar projetos/clientes passados

### RF10 — Tracking de desfecho e win-rate
- `POST /opportunities/{id}/outcome` grava `{outcome, recorded_at, notes}` na coleção `outcomes`
- `outcome` ∈ {ganhou, perdeu, sem_resposta}
- `GET /stats/win-rate` agrega taxa de vitória (won/total %) + contadores
- Campo `win_probability` reservado na Opportunity (ainda não populado — gancho para ML futuro)

### RF11 — Notificação Telegram
- Após cada coleta, `TelegramNotifier` envia as **top 5 vagas APLICAR** (ordenadas por score) para o chat configurado
- Mensagem inclui ícone de urgência (🔥/⚡/❄️), score, área, orçamento, ✅ payment verified, nº propostas e link
- Inerte (no-op) se `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` ausentes — falha silenciosa logada

### RF12 — Fontes Upwork e Workana
- **Upwork:** GraphQL oficial (`api.upwork.com/graphql`), exige OAuth2 Bearer; **desativado por padrão** (`sources.upwork: false`) — inerte sem token
- **Workana:** endpoint `/jobs` chamado como XHR (`X-Requested-With`) devolve JSON; parsing de HTML/datas relativas; até 3 páginas; ativado por padrão

---

## Endpoints da API (estado real)

| Método | Rota | Função |
|--------|------|--------|
| GET | `/health` | healthcheck |
| POST | `/api/collect` | coleta → classifica → fraude → cliente → avalia → salva → notifica |
| GET | `/api/opportunities` | lista (filtros: area, decision, source; ordena por score) |
| GET | `/api/opportunities/{id}` | detalhe |
| POST | `/api/opportunities/{id}/recalculate` | reclassifica + reavalia |
| POST | `/api/opportunities/{id}/proposal` | gera proposta dupla (Gemini Pro) |
| POST | `/api/opportunities/{id}/outcome` | registra desfecho |
| GET | `/api/stats/win-rate` | métricas de conversão |

---

## Pipeline de coleta (estado real)

```
POST /api/collect
  └─ Collector.collect_all()      → fontes em paralelo (asyncio.gather, erro isolado)
       └─ _filter()               → idioma PT/EN + orçamento mínimo
  └─ process_job() por vaga (Semaphore=8 chamadas Gemini concorrentes):
       1. firestore.exists()      → dedup por external_id        → skipped_duplicate
       2. Classifier (Flash)      → área; "Irrelevante"          → skipped_irrelevant
       3. FraudDetector (Flash)   → risk_score > 80              → skipped_fraud
       4. ClientAnalyzer (heur.)  → score cliente + urgência
       5. Evaluator (Flash)       → score 0–100 + decisão + summary
       6. firestore.save()                                       → saved
  └─ TelegramNotifier.notify_top_opportunities(novas APLICAR)
```

---

## Frontend (estado real)

- Proxy via App Router catch-all: `app/api/[...path]/route.ts` (substituiu rewrites do Next)
- Componentes: `OpportunityTable`, `ScoreBadge`, `FilterBar`, `CollectButton`, `ClientScoreBar`, `UrgencyBadge`, `OutcomeTracker`, `RecalculateButton`, `OpportunityDetail`
- Páginas: ranking (`/`) e detalhe (`/opportunities/[id]`)
- `lib/api.ts` cobre todos os 8 endpoints

---

## Infra & CI/CD (estado real)

- **Terraform:** Cloud Run (backend+frontend), Firestore, Secret Manager, Artifact Registry, WIF, backend de estado em GCS
- **GitHub Actions** (`deploy.yml`): 3 jobs
  1. `test` — pytest + cobertura (todo PR/push)
  2. `infra` — terraform apply (só main, via WIF)
  3. `deploy` — build/push imagens + `gcloud run deploy` (só main; segredos não expostos ao CI)

---

## Gaps / dívidas identificadas na varredura

| Item | Observação | Severidade |
|------|-----------|-----------|
| `win_probability` | Campo existe mas nunca é calculado — outcomes coletados mas não realimentam score | Média (feature incompleta) |
| `ClientAnalyzer` sem testes | `test_sources.py` cobre fontes, mas client_analyzer (216 linhas, mais complexo) não tem teste dedicado | Média |
| Sem autenticação | API `/api/collect` e mutações abertas (`allow_origins=["*"]`) — ok p/ uso pessoal, **bloqueador** p/ multiusuário | Alta (se virar SaaS) |
| `collector.py` usa `print` | Resto do código usa `logging`; inconsistente | Baixa |
| Firestore índices compostos | `list_opportunities` com filtro + order_by score pode exigir índice composto não provisionado no Terraform | Média |
| Recalculate não refaz fraude/cliente | `recalculate` só reclassifica+reavalia; não atualiza fraud/client | Baixa |
| `outcomes` sem dedup | Múltiplos outcomes para a mesma vaga são todos contados no win-rate | Baixa |

---

## Fora do escopo (ainda não construído)

| Feature | Status |
|---------|--------|
| Cloud Scheduler (coleta automática agendada) | Não implementado — coleta ainda é manual |
| Firebase Auth / multiusuário | Não implementado |
| LangGraph / CrewAI (orquestração formal) | Não — pipeline é `asyncio` puro |
| ML real para `win_probability` | Não — campo reservado |
| Cloud SQL PostgreSQL | Não — segue em Firestore |
| Pub/Sub | Não — coleta síncrona |
