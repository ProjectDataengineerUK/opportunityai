"use client";

import { useState } from "react";
import Link from "next/link";
import { Opportunity, ProposalResult, generateProposal } from "@/lib/api";
import { ScoreBadge } from "@/components/ScoreBadge";
import { RecalculateButton } from "@/components/RecalculateButton";

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
  const color = risk >= 70 ? "red" : "yellow";
  const label = risk >= 70 ? "Alto risco de golpe" : "Atenção — possível golpe";
  return (
    <div
      className={`border rounded-lg p-4 mb-6 ${
        color === "red"
          ? "bg-red-50 border-red-200"
          : "bg-yellow-50 border-yellow-200"
      }`}
    >
      <p
        className={`text-sm font-semibold mb-1 ${
          color === "red" ? "text-red-800" : "text-yellow-800"
        }`}
      >
        ⚠ {label} — risco {Math.round(risk)}/100
      </p>
      {flags.length > 0 && (
        <ul
          className={`text-sm list-disc list-inside space-y-0.5 ${
            color === "red" ? "text-red-700" : "text-yellow-700"
          }`}
        >
          {flags.map((f) => (
            <li key={f}>{f}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

function ProposalSection({ opportunityId, initial }: { opportunityId: string; initial: string | null }) {
  const [proposal, setProposal] = useState<string | null>(initial);
  const [meta, setMeta] = useState<Pick<ProposalResult, "suggested_price" | "estimated_hours"> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const result = await generateProposal(opportunityId);
      setProposal(result.proposal);
      setMeta({ suggested_price: result.suggested_price, estimated_hours: result.estimated_hours });
    } catch {
      setError("Falha ao gerar proposta. Tente novamente.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mt-6 border-t border-gray-100 pt-6">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-gray-700">Proposta gerada pela IA</h2>
        <button
          onClick={handleGenerate}
          disabled={loading}
          className="inline-flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <span className="inline-block h-3.5 w-3.5 rounded-full border-2 border-white border-t-transparent animate-spin" />
              Gerando…
            </>
          ) : proposal ? (
            "↻ Regerar Proposta"
          ) : (
            "✦ Gerar Proposta"
          )}
        </button>
      </div>

      {error && <p className="text-xs text-red-500 mb-2">{error}</p>}

      {proposal && (
        <div className="space-y-3">
          {meta && (meta.suggested_price || meta.estimated_hours) && (
            <div className="flex gap-4 text-sm text-gray-600">
              {meta.suggested_price && (
                <span className="bg-green-50 text-green-800 px-2 py-0.5 rounded font-mono">
                  USD {meta.suggested_price.toLocaleString()}
                </span>
              )}
              {meta.estimated_hours && (
                <span className="bg-gray-100 text-gray-700 px-2 py-0.5 rounded">
                  ~{meta.estimated_hours}h
                </span>
              )}
            </div>
          )}
          <textarea
            readOnly
            value={proposal}
            rows={8}
            className="w-full text-sm text-gray-800 bg-gray-50 border border-gray-200 rounded-lg p-4 resize-y font-sans leading-relaxed"
          />
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
        <div className="flex items-start justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{opp.title}</h1>
            <p className="text-gray-500 text-sm mt-1 capitalize">{opp.source}</p>
          </div>
          <div className="flex flex-col items-end gap-3">
            <ScoreBadge score={opp.score} decision={opp.decision} />
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
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Breakdown do score</h2>
          <div className="space-y-2">
            <ScoreRow label="Compatibilidade skills" value={sb.skill_match} />
            <ScoreRow label="Orçamento" value={sb.budget} />
            <ScoreRow label="Chance de fechar" value={sb.close_chance} />
            <ScoreRow label="Baixa concorrência" value={sb.competition} />
            <ScoreRow label="Clareza da vaga" value={sb.clarity} />
          </div>
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

        <ProposalSection opportunityId={opp.id} initial={opp.proposal ?? null} />
      </div>
    </main>
  );
}
