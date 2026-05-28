"use client";

import Link from "next/link";
import { Opportunity } from "@/lib/api";
import { ScoreBadge } from "./ScoreBadge";

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
  IA: "bg-purple-100 text-purple-700",
  Dados: "bg-blue-100 text-blue-700",
  Python: "bg-yellow-100 text-yellow-700",
  Backend: "bg-green-100 text-green-700",
  Automação: "bg-orange-100 text-orange-700",
  Cloud: "bg-sky-100 text-sky-700",
};

export function OpportunityTable({ opportunities }: OpportunityTableProps) {
  if (opportunities.length === 0) {
    return (
      <div className="text-center py-16 text-gray-400">
        <p className="text-lg">Nenhuma vaga encontrada.</p>
        <p className="text-sm mt-1">Clique em &ldquo;Coletar Vagas&rdquo; para buscar oportunidades.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-gray-100 shadow-sm">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 text-gray-500 uppercase text-xs tracking-wide">
          <tr>
            <th className="px-4 py-3 text-left">Score</th>
            <th className="px-4 py-3 text-left">Título</th>
            <th className="px-4 py-3 text-left">Área</th>
            <th className="px-4 py-3 text-left">Plataforma</th>
            <th className="px-4 py-3 text-left">Orçamento</th>
            <th className="px-4 py-3 text-left">Ação</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {opportunities.map((opp) => (
            <tr key={opp.id} className="hover:bg-gray-50 transition-colors">
              <td className="px-4 py-3">
                <ScoreBadge score={opp.score} decision={opp.decision} />
              </td>
              <td className="px-4 py-3 max-w-xs">
                <Link
                  href={`/opportunities/${opp.id}`}
                  className="font-medium text-gray-900 hover:text-blue-600 line-clamp-2"
                >
                  {opp.title}
                </Link>
              </td>
              <td className="px-4 py-3">
                <span
                  className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                    AREA_COLORS[opp.area] || "bg-gray-100 text-gray-600"
                  }`}
                >
                  {opp.area}
                </span>
              </td>
              <td className="px-4 py-3 text-gray-500 capitalize">{opp.source}</td>
              <td className="px-4 py-3 text-gray-700 font-mono text-xs">{formatBudget(opp)}</td>
              <td className="px-4 py-3">
                <a
                  href={opp.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline text-xs"
                >
                  Ver vaga →
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
