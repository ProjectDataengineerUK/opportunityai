# BRAINSTORM — OpportunityAI MVP

**Data:** 2026-05-28  
**Status:** Completo — pronto para `/define`  
**Feature:** MVP pessoal cloud-native GCP

---

## Contexto

App para selecionar automaticamente as melhores oportunidades freelance em IA, Dados e Programação. O usuário é o próprio freelancer — começa como ferramenta pessoal, valida a dor real, depois expande para SaaS.

---

## O que foi descoberto

### Cenário de uso
- **Fase 1 (MVP):** Uso pessoal — o próprio desenvolvedor usa para filtrar vagas
- **Fase 2:** Validação da dor + gerador de proposta
- **Fase 3:** SaaS — outros freelancers se cadastram e usam

### Fluxo MVP
```
Cloud Scheduler (trigger periódico)
    ↓
Cloud Run — Agente Coletor
    ├── RemoteOK API (gratuita, sem auth)
    ├── Remotive API (gratuita, sem auth)
    └── Freelancer API (OAuth, requer app cadastrado)
    ↓
Cloud Run — Agente Avaliador (Gemini 2.5 Flash)
    ↓
Firestore (armazenamento)
    ↓
Dashboard Next.js (Cloud Run ou Firebase Hosting)
```

### Infraestrutura GCP
| Serviço | Uso |
|---------|-----|
| Cloud Run | Backend FastAPI + workers de coleta/avaliação |
| Firestore | Banco de dados das vagas e scores |
| Cloud Scheduler | Trigger de coleta periódica |
| Secret Manager | Chaves Freelancer API + Gemini API |
| Gemini 2.5 Flash | Scoring, classificação de vagas |
| Gemini 2.5 Pro | Análises mais complexas (opcional no MVP) |
| Terraform | Provisionamento de toda a infra |

---

## Score configurável

Arquivo `config.yaml` com pesos ajustáveis:

```yaml
score_weights:
  budget: 0.25          # orçamento vs. seu mínimo
  skill_match: 0.35     # compatibilidade com perfil Python/IA/dados
  close_chance: 0.20    # histórico do cliente + clareza da vaga
  competition: 0.10     # número de propostas já enviadas
  clarity: 0.10         # descrição clara e bem estruturada
```

O usuário edita diretamente o arquivo no início — sem interface de configuração no MVP.

---

## Fontes de dados

| API | Auth | Custo | Foco |
|-----|------|-------|------|
| RemoteOK | Nenhuma | Gratuito | Remote tech jobs |
| Remotive | Nenhuma | Gratuito | Remote jobs (Software, Data, AI) |
| Freelancer | OAuth 2.0 | Gratuito (tier básico) | Projetos freelance globais |

> **Nota Freelancer API:** Requer cadastro em developers.freelancer.com e criação de app OAuth. Adiciona ~2h de setup a mais que as outras duas.

---

## Dashboard — telas MVP

### 1. Ranking de oportunidades
```
Score | Título           | Plataforma  | Área  | Orçamento | Decisão
92    | Python Automation | Freelancer  | IA    | $500      | APLICAR
78    | Data Pipeline Job | RemoteOK    | Dados | $1200     | AVALIAR
31    | Quick React fix   | Remotive    | Web   | $50       | IGNORAR
```

### 2. Detalhe da vaga
- Resumo gerado pelo Gemini
- Justificativa do score
- Skills exigidas vs. skills do perfil
- Link para a vaga original

### 3. Filtros
- Por área (IA / Dados / Python / Backend / Automação)
- Score mínimo
- Plataforma
- Data de publicação

---

## YAGNI — O que foi removido do MVP

| Feature removida | Motivo |
|-----------------|--------|
| Firebase Auth | Uso pessoal — sem necessidade de login |
| Pub/Sub | Overkill para MVP; Cloud Scheduler + Cloud Run direto é suficiente |
| LangGraph / CrewAI multiagentes | Funções Python simples funcionam igual no MVP |
| Gerador de proposta | Fase 2 — primeiro valida o score |
| Anti-golpe com IA | MVP usa flags por palavras-chave; IA só na fase SaaS |
| Cloud SQL PostgreSQL | Firestore é suficiente para MVP pessoal |
| Upwork API | Requer parceria especial — fora do MVP |
| Workana API | Documentação limitada — fora do MVP |
| Interface de config de pesos | Edita config.yaml diretamente no MVP |

---

## Abordagem escolhida

**GCP direto desde o dia 1** — sem fase local antes.

O usuário prefere já estar na infraestrutura final mesmo com o overhead inicial de setup. Terraform automatiza o provisionamento para minimizar a fricção.

**Ordem de implementação:**
1. Terraform: projeto GCP + Cloud Run + Firestore + Secret Manager
2. Agente Coletor: RemoteOK + Remotive (sem auth, mais rápido)
3. Dashboard Next.js básico consumindo dados reais
4. Agente Avaliador com Gemini 2.5 Flash + config.yaml de pesos
5. Integração Freelancer API (OAuth)
6. Filtros e detalhe de vaga no dashboard

---

## Perfil de skills (a definir no `/define`)

O Avaliador precisa de um perfil base para calcular `skill_match`. Como não há perfil documentado, o `/define` deve capturar:
- Skills principais do usuário
- Valor mínimo aceitável por projeto (R$ ou USD)
- Idiomas aceitos
- Áreas de interesse prioritárias

---

## Rascunho de requisitos

### Funcionais
- [ ] Coletar vagas automaticamente em RemoteOK, Remotive e Freelancer API
- [ ] Classificar vagas por área (IA, Dados, Python, Backend, Automação, Irrelevante)
- [ ] Calcular score 0–100 com pesos configuráveis por critério
- [ ] Armazenar vagas e scores no Firestore
- [ ] Exibir ranking ordenado por score no dashboard
- [ ] Filtrar vagas por área, score mínimo, plataforma e data
- [ ] Exibir detalhe da vaga com resumo gerado pelo Gemini
- [ ] Trigger periódico de coleta via Cloud Scheduler

### Não-funcionais
- [ ] Infraestrutura 100% GCP, provisionada via Terraform
- [ ] Gemini 2.5 Flash para scoring (Gemini 2.5 Pro opcional para análises pesadas)
- [ ] Chaves de API gerenciadas pelo Secret Manager
- [ ] Sem autenticação no MVP (uso pessoal)
- [ ] Score configurável via `config.yaml` sem redeploy

---

## Próximos passos

```bash
/define .claude/sdd/features/BRAINSTORM_OPPORTUNITYAI_MVP.md
```

Captura os requisitos formais, define o perfil de skills do usuário e detalha os contratos de dados entre os agentes.
