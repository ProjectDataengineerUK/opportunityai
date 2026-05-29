"use client";

import { useEffect, useState, useCallback } from "react";
import { listOpportunities, Opportunity, CollectResult, getWinRate, WinRateStats } from "@/lib/api";
import { OpportunityTable } from "@/components/OpportunityTable";
import { FilterBar } from "@/components/FilterBar";
import { CollectButton } from "@/components/CollectButton";

export default function DashboardPage() {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [collectError, setCollectError] = useState<string | null>(null);
  const [lastCollect, setLastCollect] = useState<CollectResult | null>(null);
  const [lastCollectTime, setLastCollectTime] = useState<string | null>(null);
  const [winRate, setWinRate] = useState<WinRateStats | null>(null);
  const [area, setArea] = useState("all");
  const [decision, setDecision] = useState("all");
  const [source, setSource] = useState("all");

  const fetchOpportunities = useCallback(async () => {
    setLoading(true);
    setFetchError(null);
    try {
      const data = await listOpportunities({
        area: area !== "all" ? area : undefined,
        decision: decision !== "all" ? decision : undefined,
        source: source !== "all" ? source : undefined,
      });
      setOpportunities(data);
    } catch (e) {
      setFetchError(e instanceof Error ? e.message : "Erro ao carregar vagas.");
    } finally {
      setLoading(false);
    }
  }, [area, decision, source]);

  useEffect(() => {
    fetchOpportunities();
    getWinRate().then(setWinRate).catch(() => {});
  }, [fetchOpportunities]);

  function handleCollectComplete(result: CollectResult) {
    setLastCollect(result);
    setLastCollectTime(new Date().toLocaleTimeString("pt-BR"));
    setCollectError(null);
    fetchOpportunities();
  }

  function handleCollectError(msg: string) {
    setCollectError(msg);
  }

  const aplicar = opportunities.filter((o) => o.decision === "APLICAR").length;
  const avaliar = opportunities.filter((o) => o.decision === "AVALIAR").length;
  const quente = opportunities.filter((o) => o.urgency === "quente").length;

  return (
    <main className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">OpportunityAI</h1>
        <p className="text-gray-500 mt-1">Vagas freelance em IA, Dados e Programação — ranqueadas por IA</p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
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
        <div className="bg-white rounded-xl border border-orange-100 p-5 shadow-sm">
          <p className="text-sm text-orange-600">
            {quente > 0 ? "🔥 Vagas quentes" : winRate?.win_rate !== null && winRate?.win_rate !== undefined ? "Taxa de ganho" : "Vagas quentes"}
          </p>
          <p className="text-3xl font-bold mt-1 text-orange-700">
            {quente > 0
              ? quente
              : winRate?.win_rate !== null && winRate?.win_rate !== undefined
              ? `${winRate.win_rate}%`
              : "—"}
          </p>
          {winRate && winRate.total > 0 && quente === 0 && (
            <p className="text-xs text-gray-400 mt-1">{winRate.total} propostas registradas</p>
          )}
        </div>
      </div>

      {collectError && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded-xl p-4">
          <p className="text-sm font-semibold text-red-800 mb-1">Falha ao coletar vagas</p>
          <p className="text-sm text-red-700 font-mono">{collectError}</p>
          <p className="text-xs text-red-500 mt-1">
            Verifique os logs do Cloud Run em: <code>GCP Console → Cloud Run → opportunityai-backend → Logs</code>
          </p>
        </div>
      )}

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
                {lastCollectTime} — {lastCollect.saved} novas · {lastCollect.skipped_duplicate} dup · {lastCollect.skipped_fraud} fraude
              </span>
            )}
            <CollectButton onComplete={handleCollectComplete} onError={handleCollectError} />
          </div>
        </div>

        {fetchError ? (
          <div className="text-center py-16">
            <p className="text-red-500 text-sm font-medium">{fetchError}</p>
            <button
              onClick={fetchOpportunities}
              className="mt-3 text-sm text-blue-600 hover:underline"
            >
              Tentar novamente
            </button>
          </div>
        ) : loading ? (
          <div className="text-center py-16 text-gray-400">Carregando vagas…</div>
        ) : (
          <OpportunityTable opportunities={opportunities} />
        )}
      </div>
    </main>
  );
}
