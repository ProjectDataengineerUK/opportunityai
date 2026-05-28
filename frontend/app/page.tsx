"use client";

import { useEffect, useState, useCallback } from "react";
import { listOpportunities, Opportunity, CollectResult } from "@/lib/api";
import { OpportunityTable } from "@/components/OpportunityTable";
import { FilterBar } from "@/components/FilterBar";
import { CollectButton } from "@/components/CollectButton";

export default function DashboardPage() {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastCollect, setLastCollect] = useState<CollectResult | null>(null);
  const [lastCollectTime, setLastCollectTime] = useState<string | null>(null);
  const [area, setArea] = useState("all");
  const [decision, setDecision] = useState("all");
  const [source, setSource] = useState("all");

  const fetchOpportunities = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listOpportunities({
        area: area !== "all" ? area : undefined,
        decision: decision !== "all" ? decision : undefined,
        source: source !== "all" ? source : undefined,
      });
      setOpportunities(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [area, decision, source]);

  useEffect(() => {
    fetchOpportunities();
  }, [fetchOpportunities]);

  function handleCollectComplete(result: CollectResult) {
    setLastCollect(result);
    setLastCollectTime(new Date().toLocaleTimeString("pt-BR"));
    fetchOpportunities();
  }

  const aplicar = opportunities.filter((o) => o.decision === "APLICAR").length;
  const avaliar = opportunities.filter((o) => o.decision === "AVALIAR").length;

  return (
    <main className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">OpportunityAI</h1>
        <p className="text-gray-500 mt-1">Vagas freelance em IA, Dados e Programação — ranqueadas por IA</p>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
          <p className="text-sm text-gray-500">Total de vagas</p>
          <p className="text-3xl font-bold mt-1">{opportunities.length}</p>
        </div>
        <div className="bg-white rounded-xl border border-green-100 p-5 shadow-sm">
          <p className="text-sm text-green-600">APLICAR agora</p>
          <p className="text-3xl font-bold mt-1 text-green-700">{aplicar}</p>
        </div>
        <div className="bg-white rounded-xl border border-yellow-100 p-5 shadow-sm">
          <p className="text-sm text-yellow-600">AVALIAR</p>
          <p className="text-3xl font-bold mt-1 text-yellow-700">{avaliar}</p>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-100 p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
          <FilterBar
            area={area}
            decision={decision}
            source={source}
            onAreaChange={setArea}
            onDecisionChange={setDecision}
            onSourceChange={setSource}
          />
          <div className="flex items-center gap-4">
            {lastCollect && lastCollectTime && (
              <span className="text-xs text-gray-400">
                Última coleta {lastCollectTime} — {lastCollect.saved} novas vagas
              </span>
            )}
            <CollectButton onComplete={handleCollectComplete} />
          </div>
        </div>

        {loading ? (
          <div className="text-center py-16 text-gray-400">Carregando vagas…</div>
        ) : (
          <OpportunityTable opportunities={opportunities} />
        )}
      </div>
    </main>
  );
}
