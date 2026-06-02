"use client";

import { useState } from "react";
import Link from "next/link";
import { Opportunity, ProposalResult, generateProposal } from "@/lib/api";
import { ScoreBadge } from "@/components/ScoreBadge";
import { RecalculateButton } from "@/components/RecalculateButton";
import { UrgencyBadge } from "@/components/UrgencyBadge";
import { ClientScoreBar } from "@/components/ClientScoreBar";
import { OutcomeTracker } from "@/components/OutcomeTracker";

function ScoreRow({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center gap-3">
      <span className="text-sm text-gray-500 w-36">{label}</span>
      <div className="flex-1 bg-gray-100 rounded-full h-2">
        <div
          className="bg-blue-500 h-2 rounded-full transition-all"
          style={{ width: `${Math.min(100, value)}%` }}
        />
      </div>
      <span className="text-sm font-mono w-10 text-right">{Math.round(value)}</span>
    </div>
  );
}

function FraudWarning({ risk, flags }: { risk: number; flags: string[] }) {
  if (risk < 30) return null;
  const isHigh = risk >= 70;
  return (
    <div className={`border rounded-lg p-4 mb-6 ${isHigh ? "bg-red-50 border-red-200" : "bg-yellow-50 border-yellow-200"}`}>
      <p className={`text-sm font-semibold mb-1 ${isHigh ? "text-red-800" : "text-yellow-800"}`}>
        ⚠ {isHigh ? "Alto risco de golpe" : "Atenção — possível golpe"} — risco {Math.round(risk)}/100
      </p>
      {flags.length > 0 && (
        <ul className={`text-sm list-disc list-inside space-y-0.5 ${isHigh ? "text-red-700" : "text-yellow-700"}`}>
          {flags.map((f) => <li key={f}>{f}</li>)}
        </ul>
      )}
    </div>
  );
}

type ProposalStyle = "direct" | "consultive";

function ProposalSection({
  opportunityId,
  initialResult,
}: {
  opportunityId: string;
  initialResult: Pick<Opportunity, "proposal" | "proposal_direct" | "proposal_consultive" | "suggested_price" | "estimated_hours">;
}) {
  const [result, setResult] = useState<ProposalResult | null>(
    initialResult.proposal_direct
      ? {
          proposal: initialResult.proposal ?? "",
          proposal_direct: initialResult.proposal_direct,
          proposal_consultive: initialResult.proposal_consultive ?? "",
          suggested_price: initialResult.suggested_price,
          estimated_hours: initialResult.estimated_hours,
        }
      : null
  );
  const [style, setStyle] = useState<ProposalStyle>("direct");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [proposed, setProposed] = useState(false);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const r = await generateProposal(opportunityId);
      setResult(r);
      setProposed(false);
    } catch {
      setError("Falha ao gerar proposta. Tente novamente.");
    } finally {
      setLoading(false);
    }
  }

  const activeText = style === "direct" ? result?.proposal_direct : result?.proposal_consultive;

  return (
    <div className="mt-6 border-t border-gray-100 pt-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-gray-700">Proposta gerada pela IA</h2>
        <button
          onClick={handleGenerate}
          disabled={loading}
          className="inline-flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
        >
          {loading ? (
            <><span className="inline-block h-3.5 w-3.5 rounded-full border-2 border-white border-t-transparent animate-spin" />Gerando…</>
          ) : result ? "↻ Regerar" : "✦ Gerar Proposta"}
        </button>
      </div>

      {error && <p className="text-xs text-red-500 mb-3">{error}</p>}

      {result && (
        <div className="space-y-4">
          {(result.suggested_price || result.estimated_hours) && (
            <div className="flex gap-3 text-sm">
              {result.suggested_price && (
                <span className="bg-green-50 text-green-800 px-3 py-1 rounded-lg font-mono border border-green-100">
                  USD {result.suggested_price.toLocaleString()}
                </span>
              )}
              {result.estimated_hours && (
                <span className="bg-gray-100 text-gray-700 px-3 py-1 rounded-lg">
                  ~{result.estimated_hours}h
                </span>
              )}
            </div>
          )}

          <div className="flex gap-1 bg-gray-100 p-1 rounded-lg w-fit">
            <button
              onClick={() => setStyle("direct")}
              className={`text-xs font-medium px-3 py-1.5 rounded-md transition-colors ${style === "direct" ? "bg-white shadow-sm text-gray-900" : "text-gray-500 hover:text-gray-700"}`}
            >
              Direto
            </button>
            <button
              onClick={() => setStyle("consultive")}
              className={`text-xs font-medium px-3 py-1.5 rounded-md transition-colors ${style === "consultive" ? "bg-white shadow-sm text-gray-900" : "text-gray-500 hover:text-gray-700"}`}
            >
              Consultivo
            </button>
          </div>

          <textarea
            readOnly
            value={activeText ?? ""}
            rows={9}
            className="w-full text-sm text-gray-800 bg-gray-50 border border-gray-200 rounded-lg p-4 resize-y font-sans leading-relaxed"
          />

          <div
            className="text-xs text-gray-400 cursor-pointer hover:text-gray-600 select-none"
            onClick={() => {
              if (activeText) {
                navigator.clipboard.writeText(activeText);
                setProposed(true);
                setTimeout(() => setProposed(false), 2000);
              }
            }}
          >
            {proposed ? "✓ Copiado!" : "Clique para copiar"}
          </div>
        </div>
      )}

      {result && (
        <div className="mt-6 pt-4 border-t border-gray-100">
          <OutcomeTracker opportunityId={opportunityId} />
        </div>
      )}
    </div>
  );
}

export function OpportunityDetail({ initial }: { initial: Opportunity }) {
  const [opp, setOpp] = useState(initial);
  const sb = opp.score_breakdown;

  return (
    <main className="max-w-3xl mx-auto px-4 py-8">
      <Link href="/" className="text-sm text-blue-600 hover:underline mb-6 block">
        ← Voltar ao ranking
      </Link>

      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-8">
        <div className="flex items-start justify-between gap-4 mb-2">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{opp.title}</h1>
            <div className="flex items-center gap-2 mt-1">
              <p className="text-gray-500 text-sm capitalize">{opp.source}</p>
              {opp.urgency !== "normal" && (
                <UrgencyBadge
                  urgency={opp.urgency}
                  proposalsCount={opp.proposals_count}
                  postedAt={opp.posted_at}
                />
              )}
              {opp.proposals_count !== null && opp.urgency === "normal" && (
                <span className="text-xs text-gray-400">{opp.proposals_count} propostas</span>
              )}
            </div>
          </div>
          <div className="flex flex-col items-end gap-3">
            <ScoreBadge score={opp.score} decision={opp.decision} />
            {opp.win_probability != null && (
              <span className="text-xs text-gray-500" title="Chance estimada de fechar, baseada no histórico de desfechos">
                Chance: <span className="font-semibold text-gray-700">{Math.round(opp.win_probability * 100)}%</span>
              </span>
            )}
            <RecalculateButton id={opp.id} onComplete={setOpp} />
          </div>
        </div>

        <FraudWarning risk={opp.fraud_risk ?? 0} flags={opp.fraud_flags ?? []} />

        {opp.summary && (
          <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 mb-6">
            <p className="text-sm font-medium text-blue-800 mb-1">Análise da IA</p>
            <p className="text-sm text-blue-700">{opp.summary}</p>
          </div>
        )}

        <div className="mb-6">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Score da vaga</h2>
          <div className="space-y-2">
            <ScoreRow label="Compatibilidade skills" value={sb.skill_match} />
            <ScoreRow label="Orçamento" value={sb.budget} />
            <ScoreRow label="Chance de fechar" value={sb.close_chance} />
            <ScoreRow label="Baixa concorrência" value={sb.competition} />
            <ScoreRow label="Clareza da vaga" value={sb.clarity} />
          </div>
        </div>

        <div className="mb-6 border-t border-gray-100 pt-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Score do cliente</h2>
          <ClientScoreBar
            score={opp.client_score ?? 0}
            hireRate={opp.client_hire_rate ?? null}
            paymentVerified={opp.client_payment_verified ?? false}
            totalSpent={opp.client_total_spent ?? null}
          />
        </div>

        {opp.skills_required?.length > 0 && (
          <div className="mb-6">
            <h2 className="text-sm font-semibold text-gray-700 mb-2">Skills exigidas</h2>
            <div className="flex flex-wrap gap-2">
              {opp.skills_required.map((skill) => (
                <span key={skill} className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded-md">
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}

        {opp.budget_min && (
          <div className="mb-6">
            <h2 className="text-sm font-semibold text-gray-700 mb-1">Orçamento</h2>
            <p className="text-gray-800 font-mono">
              {opp.budget_currency || "USD"} {opp.budget_min.toLocaleString()}
              {opp.budget_max ? ` – ${opp.budget_max.toLocaleString()}` : "+"}
            </p>
          </div>
        )}

        <a
          href={opp.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-5 py-2.5 rounded-lg transition-colors"
        >
          Ver vaga original →
        </a>

        <ProposalSection opportunityId={opp.id!} initialResult={opp} />
      </div>
    </main>
  );
}
