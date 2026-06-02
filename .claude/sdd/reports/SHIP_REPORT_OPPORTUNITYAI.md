# SHIP REPORT — OpportunityAI (MVP + V2)

**Data:** 2026-05-31
**Status:** MVP entregue e superado · V2 em produção-ready (não deployado/validado em GCP real)
**Docs:** BRAINSTORM → DEFINE (MVP) → DESIGN (MVP) → BUILD (28/05) → DEFINE_V2 (engenharia reversa)

---

## O que foi entregue

### Ciclo 1 — MVP (planejado via SDD, concluído 2026-05-28)
Coleta (RemoteOK/Remotive/Freelancer) → classificação por área (Gemini Flash) → score 0–100 ponderado por `config.yaml` → decisão APLICAR/AVALIAR/IGNORAR → dashboard Next.js com ranking, filtros e detalhe → infra Terraform na GCP. 41 arquivos, AT01–AT06 cobertos.

### Ciclo 2 — V2 (construído fora do fluxo SDD, 29–31/05)
Documentado em `DEFINE_OPPORTUNITYAI_V2.md`. Resumo:
- **Detecção de fraude com IA** (descarta risk > 80)
- **Análise de cliente** (score, hire rate, payment verified, total spent) **+ urgência** (quente/normal/frio)
- **Proposta dupla** (direta + consultiva) com preço e horas sugeridos (Gemini Pro)
- **Tracking de desfecho** + endpoint de win-rate
- **Notificação Telegram** das top vagas APLICAR
- **+2 fontes:** Upwork (GraphQL/OAuth2, off por padrão) e Workana (XHR scraping)
- **CI/CD completo:** test → terraform → deploy via WIF, sem segredos no CI

---

## Estado verificado (varredura 2026-05-31)

| Dimensão | Estado |
|----------|--------|
| Backend | 1.862 linhas Python · 6 agentes · 3 serviços · 8 endpoints |
| Testes | **33 passando** (evaluator, classifier, fraud, proposal, sources) |
| Fontes | 5 (3 ativas, Upwork off, Workana scraping) |
| Frontend | Next.js App Router, 9 componentes, proxy catch-all |
| Infra | Terraform + GCS state + WIF + Artifact Registry |
| Deploy real em GCP | ⚠️ Não confirmado nesta varredura (código pronto) |

---

## Decisões de arquitetura que se mantiveram

1. **`asyncio` puro em vez de LangGraph/CrewAI** — pipeline de coleta com `gather` + `Semaphore(8)`; multiagentes formais não foram necessários.
2. **Firestore (não Cloud SQL)** — suficiente para o volume atual.
3. **Coleta manual (não Cloud Scheduler)** — disparo por botão; agendamento adiado.
4. **Heurística para cliente, LLM para fraude/score/proposta** — `ClientAnalyzer` é determinístico (rápido/grátis); só o que exige julgamento vai pro Gemini.
5. **Falhas isoladas** — fonte que cai (`return_exceptions=True`) e job que falha não derrubam a coleta.

---

## Lições aprendidas

- ✅ **O SDD acelerou o MVP**, mas o **Ciclo 2 cresceu sem atualizar os docs** — gerou drift de 3 dias entre código e SDD. Lição: rodar `/iterate` ao adicionar feature relevante, não só no fim.
- ✅ **Separar `infra` de `deploy` no CI** evitou expor segredos ao Terraform no runner (decisão registrada em commits `ad7710a`, vários fixes de Terraform/secret).
- ⚠️ **`win_probability` ficou meio-implementado**: outcomes são coletados mas não realimentam o score. Feature em aberto, não fechar o loop é dívida.
- ⚠️ **`ClientAnalyzer` (216 linhas, o agente mais complexo) não tem teste dedicado** — risco de regressão silenciosa no parsing por fonte.

---

## Próximos passos recomendados

**Curto prazo (fechar dívidas):**
1. Teste dedicado para `ClientAnalyzer` (parsing por fonte + cálculo de score/urgência)
2. Confirmar deploy real na GCP e validar AT01/AT05 com infra de verdade
3. Provisionar índices compostos do Firestore no Terraform (filtro + order_by)

**Médio prazo (próximo ciclo SDD — usar `/define`):**
1. Fechar o loop de aprendizado: usar `outcomes` para calcular `win_probability`
2. Cloud Scheduler para coleta automática agendada
3. Se for multiusuário: Firebase Auth + restringir CORS + proteger mutações

---

## Próximo comando

```bash
# Para registrar formalmente a próxima feature (ex.: win_probability com ML):
/define "fechar loop de aprendizado: prever win_probability a partir de outcomes"
```
