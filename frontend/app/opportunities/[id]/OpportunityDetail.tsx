"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, ExternalLink, Loader2, RotateCw, Sparkles } from "lucide-react";
import { Opportunity, ProposalResult, generateProposal } from "@/lib/api";
import { ScoreBadge } from "@/components/ScoreBadge";
import { RecalculateButton } from "@/components/RecalculateButton";
import { UrgencyBadge } from "@/components/UrgencyBadge";
import { ClientScoreBar } from "@/components/ClientScoreBar";
import { OutcomeTracker } from "@/components/OutcomeTracker";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

function ScoreRow({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center gap-3">
      <span className="text-sm text-muted-foreground w-36">{label}</span>
      <div className="flex-1 bg-muted rounded-full h-2">
        <div
          className="bg-primary h-2 rounded-full transition-all"
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
    <div
      className={cn(
        "border rounded-lg p-4 mb-6",
        isHigh
          ? "bg-red-50 border-red-200 dark:bg-red-500/10 dark:border-red-500/30"
          : "bg-yellow-50 border-yellow-200 dark:bg-yellow-500/10 dark:border-yellow-500/30"
      )}
    >
      <p
        className={cn(
          "text-sm font-semibold mb-1",
          isHigh ? "text-red-800 dark:text-red-300" : "text-yellow-800 dark:text-yellow-300"
        )}
      >
        ⚠ {isHigh ? "Alto risco de golpe" : "Atenção — possível golpe"} — risco {Math.round(risk)}/100
      </p>
      {flags.length > 0 && (
        <ul
          className={cn(
            "text-sm list-disc list-inside space-y-0.5",
            isHigh ? "text-red-700 dark:text-red-400" : "text-yellow-700 dark:text-yellow-400"
          )}
        >
          {flags.map((f) => (
            <li key={f}>{f}</li>
          ))}
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
  initialResult: Pick<
    Opportunity,
    "proposal" | "proposal_direct" | "proposal_consultive" | "suggested_price" | "estimated_hours"
  >;
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
    <div className="mt-6 border-t border-border pt-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-foreground">Proposta gerada pela IA</h2>
        <Button variant="success" size="sm" onClick={handleGenerate} disabled={loading}>
          {loading ? (
            <>
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Gerando…
            </>
          ) : result ? (
            <>
              <RotateCw className="h-3.5 w-3.5" />
              Regerar
            </>
          ) : (
            <>
              <Sparkles className="h-3.5 w-3.5" />
              Gerar Proposta
            </>
          )}
        </Button>
      </div>

      {error && <p className="text-xs text-red-500 mb-3">{error}</p>}

      {result && (
        <div className="space-y-4">
          {(result.suggested_price || result.estimated_hours) && (
            <div className="flex gap-3 text-sm">
              {result.suggested_price && (
                <Badge variant="success" className="px-3 py-1 font-mono text-sm rounded-lg">
                  USD {result.suggested_price.toLocaleString()}
                </Badge>
              )}
              {result.estimated_hours && (
                <Badge variant="muted" className="px-3 py-1 text-sm rounded-lg">
                  ~{result.estimated_hours}h
                </Badge>
              )}
            </div>
          )}

          <div className="flex gap-1 bg-muted p-1 rounded-lg w-fit">
            {(["direct", "consultive"] as const).map((s) => (
              <button
                key={s}
                onClick={() => setStyle(s)}
                className={cn(
                  "text-xs font-medium px-3 py-1.5 rounded-md transition-colors",
                  style === s
                    ? "bg-card shadow-sm text-foreground"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                {s === "direct" ? "Direto" : "Consultivo"}
              </button>
            ))}
          </div>

          <textarea
            readOnly
            value={activeText ?? ""}
            rows={9}
            className="w-full text-sm text-foreground bg-muted/50 border border-border rounded-lg p-4 resize-y font-sans leading-relaxed focus:outline-none focus:ring-2 focus:ring-ring"
          />

          <button
            className="text-xs text-muted-foreground cursor-pointer hover:text-foreground select-none transition-colors"
            onClick={() => {
              if (activeText) {
                navigator.clipboard.writeText(activeText);
                setProposed(true);
                setTimeout(() => setProposed(false), 2000);
              }
            }}
          >
            {proposed ? "✓ Copiado!" : "Clique para copiar"}
          </button>
        </div>
      )}

      {result && (
        <div className="mt-6 pt-4 border-t border-border">
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
      <Link
        href="/"
        className="inline-flex items-center gap-1 text-sm text-primary hover:underline mb-6"
      >
        <ArrowLeft className="h-4 w-4" />
        Voltar ao ranking
      </Link>

      <Card className="p-8">
        <div className="flex items-start justify-between gap-4 mb-2">
          <div>
            <h1 className="text-2xl font-bold">{opp.title}</h1>
            <div className="flex items-center gap-2 mt-1">
              <p className="text-muted-foreground text-sm capitalize">{opp.source}</p>
              {opp.urgency !== "normal" && (
                <UrgencyBadge
                  urgency={opp.urgency}
                  proposalsCount={opp.proposals_count}
                  postedAt={opp.posted_at}
                />
              )}
              {opp.proposals_count !== null && opp.urgency === "normal" && (
                <span className="text-xs text-muted-foreground">{opp.proposals_count} propostas</span>
              )}
            </div>
          </div>
          <div className="flex flex-col items-end gap-3">
            <ScoreBadge score={opp.score} decision={opp.decision} />
            {opp.win_probability != null && (
              <span
                className="text-xs text-muted-foreground"
                title="Chance estimada de fechar, baseada no histórico de desfechos"
              >
                Chance:{" "}
                <span className="font-semibold text-foreground">
                  {Math.round(opp.win_probability * 100)}%
                </span>
              </span>
            )}
            <RecalculateButton id={opp.id} onComplete={setOpp} />
          </div>
        </div>

        <FraudWarning risk={opp.fraud_risk ?? 0} flags={opp.fraud_flags ?? []} />

        {opp.summary && (
          <div className="bg-primary/5 border border-primary/20 rounded-lg p-4 mb-6">
            <p className="text-sm font-medium text-primary mb-1 flex items-center gap-1.5">
              <Sparkles className="h-3.5 w-3.5" />
              Análise da IA
            </p>
            <p className="text-sm text-foreground/80">{opp.summary}</p>
          </div>
        )}

        <div className="mb-6">
          <h2 className="text-sm font-semibold text-foreground mb-3">Score da vaga</h2>
          <div className="space-y-2">
            <ScoreRow label="Compatibilidade skills" value={sb.skill_match} />
            <ScoreRow label="Orçamento" value={sb.budget} />
            <ScoreRow label="Chance de fechar" value={sb.close_chance} />
            <ScoreRow label="Baixa concorrência" value={sb.competition} />
            <ScoreRow label="Clareza da vaga" value={sb.clarity} />
          </div>
        </div>

        <div className="mb-6 border-t border-border pt-5">
          <h2 className="text-sm font-semibold text-foreground mb-3">Score do cliente</h2>
          <ClientScoreBar
            score={opp.client_score ?? 0}
            hireRate={opp.client_hire_rate ?? null}
            paymentVerified={opp.client_payment_verified ?? false}
            totalSpent={opp.client_total_spent ?? null}
          />
        </div>

        {opp.skills_required?.length > 0 && (
          <div className="mb-6">
            <h2 className="text-sm font-semibold text-foreground mb-2">Skills exigidas</h2>
            <div className="flex flex-wrap gap-2">
              {opp.skills_required.map((skill) => (
                <span
                  key={skill}
                  className="text-xs bg-muted text-foreground px-2 py-1 rounded-md"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}

        {opp.budget_min && (
          <div className="mb-6">
            <h2 className="text-sm font-semibold text-foreground mb-1">Orçamento</h2>
            <p className="text-foreground font-mono">
              {opp.budget_currency || "USD"} {opp.budget_min.toLocaleString()}
              {opp.budget_max ? ` – ${opp.budget_max.toLocaleString()}` : "+"}
            </p>
          </div>
        )}

        <Button asChild>
          <a href={opp.url} target="_blank" rel="noopener noreferrer">
            Ver vaga original
            <ExternalLink className="h-4 w-4" />
          </a>
        </Button>

        <ProposalSection opportunityId={opp.id!} initialResult={opp} />
      </Card>
    </main>
  );
}
