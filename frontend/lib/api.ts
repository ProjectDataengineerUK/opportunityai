const API_URL = "";

export interface ScoreBreakdown {
  skill_match: number;
  budget: number;
  close_chance: number;
  competition: number;
  clarity: number;
}

export interface Opportunity {
  id: string;
  external_id: string;
  source: "remoteok" | "remotive" | "freelancer" | "upwork" | "workana";
  title: string;
  description: string;
  area: string;
  score: number;
  score_breakdown: ScoreBreakdown;
  decision: "APLICAR" | "AVALIAR" | "IGNORAR";
  budget_min: number | null;
  budget_max: number | null;
  budget_currency: string | null;
  url: string;
  summary: string;
  skills_required: string[];
  language: string;
  collected_at: string;
  // Fraude
  fraud_risk: number;
  fraud_flags: string[];
  // Cliente
  client_score: number;
  client_hire_rate: number | null;
  client_payment_verified: boolean;
  client_total_spent: number | null;
  // Competição & timing
  proposals_count: number | null;
  posted_at: string | null;
  urgency: "quente" | "normal" | "frio";
  // Propostas
  proposal: string | null;
  proposal_direct: string | null;
  proposal_consultive: string | null;
  suggested_price: number | null;
  estimated_hours: number | null;
  // Aprendizado
  win_probability: number | null;
}

export interface CollectResult {
  collected: number;
  saved: number;
  skipped_duplicate: number;
  skipped_irrelevant: number;
  skipped_fraud: number;
}

export interface ProposalResult {
  proposal: string;
  proposal_direct: string;
  proposal_consultive: string;
  suggested_price: number | null;
  estimated_hours: number | null;
}

export interface WinRateStats {
  win_rate: number | null;
  total: number;
  won: number;
  lost: number;
  no_response: number;
}

export async function listOpportunities(params?: {
  area?: string;
  decision?: string;
  source?: string;
}): Promise<Opportunity[]> {
  const filtered = Object.fromEntries(
    Object.entries(params || {}).filter(([, v]) => v && v !== "all")
  );
  const qs = new URLSearchParams(filtered).toString();
  const res = await fetch(`${API_URL}/api/opportunities${qs ? `?${qs}` : ""}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Failed to fetch: ${res.status}`);
  return res.json();
}

export async function getOpportunity(id: string): Promise<Opportunity> {
  const res = await fetch(`${API_URL}/api/opportunities/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Not found: ${res.status}`);
  return res.json();
}

export async function collectOpportunities(): Promise<CollectResult> {
  const res = await fetch(`${API_URL}/api/collect`, { method: "POST" });
  if (!res.ok) throw new Error(`Collection failed: ${res.status}`);
  return res.json();
}

export async function recalculateOpportunity(id: string): Promise<Opportunity> {
  const res = await fetch(`${API_URL}/api/opportunities/${id}/recalculate`, { method: "POST" });
  if (!res.ok) throw new Error(`Recalculate failed: ${res.status}`);
  return res.json();
}

export async function generateProposal(id: string): Promise<ProposalResult> {
  const res = await fetch(`${API_URL}/api/opportunities/${id}/proposal`, { method: "POST" });
  if (!res.ok) throw new Error(`Proposal generation failed: ${res.status}`);
  return res.json();
}

export async function recordOutcome(
  id: string,
  outcome: "ganhou" | "perdeu" | "sem_resposta",
  notes = ""
): Promise<void> {
  const res = await fetch(`${API_URL}/api/opportunities/${id}/outcome`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ opportunity_id: id, outcome, notes, recorded_at: new Date().toISOString() }),
  });
  if (!res.ok) throw new Error(`Record outcome failed: ${res.status}`);
}

export async function getWinRate(): Promise<WinRateStats> {
  const res = await fetch(`${API_URL}/api/stats/win-rate`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Win rate failed: ${res.status}`);
  return res.json();
}
