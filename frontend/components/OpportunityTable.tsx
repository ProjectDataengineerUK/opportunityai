"use client";

import Link from "next/link";
import { ExternalLink } from "lucide-react";
import { Opportunity } from "@/lib/api";
import { ScoreBadge } from "./ScoreBadge";
import { UrgencyBadge } from "./UrgencyBadge";
import { WinChanceBadge } from "./WinChanceBadge";

interface OpportunityTableProps {
  opportunities: Opportunity[];
}

function formatBudget(opp: Opportunity): string {
  if (!opp.budget_min && !opp.budget_max) return "—";
  const currency = opp.budget_currency || "USD";
  if (opp.budget_min && opp.budget_max) {
    return `${currency} ${opp.budget_min.toLocaleString()}–${opp.budget_max.toLocaleString()}`;
  }
  return `${currency} ${(opp.budget_min || opp.budget_max)!.toLocaleString()}`;
}

const AREA_COLORS: Record<string, string> = {
  IA: "bg-purple-100 text-purple-700 dark:bg-purple-500/15 dark:text-purple-300",
  Dados: "bg-blue-100 text-blue-700 dark:bg-blue-500/15 dark:text-blue-300",
  Python: "bg-yellow-100 text-yellow-700 dark:bg-yellow-500/15 dark:text-yellow-300",
  Backend: "bg-green-100 text-green-700 dark:bg-green-500/15 dark:text-green-300",
  Automação: "bg-orange-100 text-orange-700 dark:bg-orange-500/15 dark:text-orange-300",
  Cloud: "bg-sky-100 text-sky-700 dark:bg-sky-500/15 dark:text-sky-300",
};

function ClientBadge({ verified, score }: { verified: boolean; score: number }) {
  if (!verified && score <= 50) return null;
  const color = score >= 70 ? "text-green-600 dark:text-green-400" : "text-yellow-600 dark:text-yellow-400";
  return (
    <span className={`text-xs ${color}`} title={`Score do cliente: ${Math.round(score)}`}>
      {verified ? "✓" : "~"}
      {Math.round(score)}
    </span>
  );
}

export function OpportunityTable({ opportunities }: OpportunityTableProps) {
  if (opportunities.length === 0) {
    return (
      <div className="text-center py-16 text-muted-foreground">
        <p className="text-lg">Nenhuma vaga encontrada.</p>
        <p className="text-sm mt-1">Clique em &ldquo;Coletar Vagas&rdquo; para buscar oportunidades.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-border">
      <table className="w-full text-sm">
        <thead className="bg-muted/60 text-muted-foreground uppercase text-xs tracking-wide">
          <tr>
            <th className="px-4 py-3 text-left font-medium">Score</th>
            <th className="px-4 py-3 text-left font-medium">Título</th>
            <th className="px-4 py-3 text-left font-medium">Área</th>
            <th className="px-4 py-3 text-left font-medium">Plataforma</th>
            <th className="px-4 py-3 text-left font-medium">Orçamento</th>
            <th className="px-4 py-3 text-left font-medium">Cliente</th>
            <th className="px-4 py-3 text-left font-medium">Chance</th>
            <th className="px-4 py-3 text-left font-medium">Ação</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {opportunities.map((opp) => (
            <tr key={opp.id} className="hover:bg-muted/40 transition-colors">
              <td className="px-4 py-3">
                <div className="flex flex-col gap-1">
                  <ScoreBadge score={opp.score} decision={opp.decision} />
                  {opp.urgency !== "normal" && (
                    <UrgencyBadge
                      urgency={opp.urgency}
                      proposalsCount={opp.proposals_count}
                      postedAt={opp.posted_at}
                    />
                  )}
                </div>
              </td>
              <td className="px-4 py-3 max-w-xs">
                <Link
                  href={`/opportunities/${opp.id}`}
                  className="font-medium text-foreground hover:text-primary line-clamp-2 transition-colors"
                >
                  {opp.title}
                </Link>
              </td>
              <td className="px-4 py-3">
                <span
                  className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                    AREA_COLORS[opp.area] || "bg-muted text-muted-foreground"
                  }`}
                >
                  {opp.area}
                </span>
              </td>
              <td className="px-4 py-3 text-muted-foreground capitalize">{opp.source}</td>
              <td className="px-4 py-3 text-foreground font-mono text-xs">{formatBudget(opp)}</td>
              <td className="px-4 py-3">
                <ClientBadge
                  verified={opp.client_payment_verified ?? false}
                  score={opp.client_score ?? 50}
                />
              </td>
              <td className="px-4 py-3">
                <WinChanceBadge probability={opp.win_probability} />
              </td>
              <td className="px-4 py-3">
                <a
                  href={opp.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-primary hover:underline text-xs"
                >
                  Ver <ExternalLink className="h-3 w-3" />
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
