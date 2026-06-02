# DEFINE — Loop de aprendizado: win_probability

**Data:** 2026-05-31
**Status:** Aprovado — pronto para build
**Input:** SHIP_REPORT_OPPORTUNITYAI.md (dívida "loop de aprendizado aberto") + DEFINE_V2 (RF10)
**Próxima fase:** Build (via agentcode `python-developer` + `python-reviewer`)

---

## Problema

O campo `win_probability` existe no modelo `Opportunity` mas **nunca é calculado**. Os desfechos (`ganhou`/`perdeu`/`sem_resposta`) são gravados na coleção `outcomes` e agregados só num win-rate global (`GET /stats/win-rate`). Não há realimentação: o histórico não informa quais vagas novas têm mais chance de conversão. O loop de aprendizado está aberto.

---

## Objetivo

Calcular, para cada oportunidade, uma `win_probability` (0.0–1.0) estimada a partir do histórico de desfechos, exibi-la no ranking, e atualizá-la à medida que novos outcomes são registrados.

---

## Restrições de contexto

- **Volume baixo de dados** — uso pessoal, dezenas/centenas de outcomes no máximo. ML pesado (modelo treinado) é overkill e instável com poucos dados.
- **Sem nova dependência pesada** — manter stack atual (sem scikit-learn/numpy se evitável; aceitável `numpy` se já transitivo).
- **Firestore** — outcomes e opportunities já estão lá.
- **Determinístico e explicável** — preferível a caixa-preta, dado o uso pessoal.

---

## Abordagem escolhida

**Bayesiano/frequentista suavizado por segmento** (não modelo treinado):

`win_probability` = taxa de vitória histórica condicionada às features categóricas da vaga, com **suavização de Laplace** (prior) para lidar com poucos/zero exemplos por segmento.

- "Ganhou" = sucesso. "Perdeu" e "sem_resposta" = não-sucesso (configurável: `sem_resposta` pode ter peso parcial).
- Segmentação por features de baixa cardinalidade: `area`, `source`, faixa de `score` (bucket), `urgency`, `client_payment_verified`.
- Fallback hierárquico: se o segmento exato tem poucos dados, recua para segmentos mais gerais → win-rate global → prior neutro (0.5).

---

## Requisitos funcionais

### RF-WP01 — Cálculo da probabilidade
- Função pura `predict_win_probability(features, history_stats) -> float` em `[0,1]`
- Combina taxa por segmento + suavização de Laplace (α configurável) + fallback hierárquico
- `sem_resposta` conta como derrota com peso configurável (default: peso 1.0 = derrota cheia)

### RF-WP02 — Estatísticas do histórico
- Serviço que lê `outcomes` + join com `opportunities` (para recuperar features no momento do outcome) e agrega contadores `(wins, total)` por segmento
- Cacheável em memória por request de coleta (não recomputar por vaga)

### RF-WP03 — Integração na coleta
- No `process_job` (collect), após o evaluator, popular `opportunity.win_probability`
- Não deve quebrar a coleta se o histórico estiver vazio (retorna prior 0.5)

### RF-WP04 — Recálculo sob demanda
- `POST /opportunities/{id}/recalculate` também atualiza `win_probability`
- Novo endpoint `POST /stats/refresh-win-probabilities` (opcional) recalcula em lote as vagas abertas quando novos outcomes chegam

### RF-WP05 — Exibição no frontend
- Coluna/badge de `win_probability` no ranking e no detalhe (ex.: "Chance: 72%")
- Não exibir se `null`

---

## Critérios de sucesso

| Critério | Como medir |
|----------|-----------|
| Sem histórico → neutro | 0 outcomes ⇒ todas as vagas recebem 0.5 |
| Segmento vencedor sobe | Área com 8/10 vitórias ⇒ vagas dessa área > 0.5 |
| Segmento perdedor desce | Fonte com 0/10 vitórias ⇒ vagas dessa fonte < 0.5 |
| Poucos dados não explodem | 1/1 vitória num segmento NÃO vira 1.0 (Laplace puxa pro prior) |
| Não quebra coleta | Coleta funciona com `outcomes` vazio |
| Determinístico | Mesmas features + mesmo histórico ⇒ mesma probabilidade |

---

## Acceptance tests

### AT-WP01 — Prior sem dados
```
DADO histórico de outcomes vazio
QUANDO win_probability é calculada para qualquer vaga
ENTÃO retorna 0.5
```

### AT-WP02 — Suavização com 1 amostra
```
DADO 1 vitória e 0 derrotas no segmento "IA"
QUANDO calcula para vaga de IA (α=1)
ENTÃO probabilidade fica entre 0.5 e 0.8 (não 1.0)
```

### AT-WP03 — Segmento forte
```
DADO 9 vitórias e 1 derrota no segmento "freelancer"
QUANDO calcula para vaga freelancer
ENTÃO probabilidade > 0.6
```

### AT-WP04 — sem_resposta conta como derrota
```
DADO 0 vitórias, 5 sem_resposta no segmento
QUANDO calcula
ENTÃO probabilidade < 0.5
```

### AT-WP05 — Fallback hierárquico
```
DADO segmento exato sem dados mas área com dados
QUANDO calcula
ENTÃO usa a taxa da área, não o prior neutro
```

---

## Fora do escopo

- Modelo de ML treinado (regressão logística/árvore) — só se o volume crescer muito
- Feature de texto/embeddings da descrição
- Re-treino automático agendado
- Calibração estatística formal (Platt scaling etc.)

---

## Arquivos afetados (previsão)

| Arquivo | Mudança |
|---------|---------|
| `backend/agents/win_predictor.py` | 🆕 função pura + montagem de segmentos |
| `backend/services/firestore.py` | join outcomes×opportunities / stats agregadas |
| `backend/routers/collect.py` | popular `win_probability` no `process_job` |
| `backend/routers/opportunities.py` | atualizar no `recalculate` (+ endpoint refresh opcional) |
| `backend/config.yaml` + `config.py` | `learning: {laplace_alpha, no_response_weight, min_samples}` |
| `backend/tests/test_win_predictor.py` | 🆕 cobre AT-WP01..05 |
| `frontend/lib/api.ts` + componente | badge de chance |
