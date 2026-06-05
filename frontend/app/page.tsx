"use client";

import { useEffect, useState, useCallback } from "react";
import { listOpportunities, Opportunity, CollectResult, getWinRate, WinRateStats } from "@/lib/api";
import { OpportunityTable } from "@/components/OpportunityTable";
import { FilterBar } from "@/components/FilterBar";
import { CollectButton } from "@/components/CollectButton";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

function StatCard({
  label,
  value,
  hint,
  accent,
}: {
  label: string;
  value: string | number;
  hint?: string;
  accent?: "default" | "green" | "yellow" | "orange";
}) {
  const accentText = {
    default: "text-muted-foreground",
    green: "text-green-600 dark:text-green-400",
    yellow: "text-yellow-600 dark:text-yellow-400",
    orange: "text-orange-600 dark:text-orange-400",
  }[accent ?? "default"];

  const valueText = {
    default: "text-foreground",
    green: "text-green-600 dark:text-green-400",
    yellow: "text-yellow-600 dark:text-yellow-400",
    orange: "text-orange-600 dark:text-orange-400",
  }[accent ?? "default"];

  return (
    <Card>
      <CardContent className="p-5">
        <p className={cn("text-sm", accentText)}>{label}</p>
        <p className={cn("text-3xl font-bold mt-1 tabular-nums", valueText)}>{value}</p>
        {hint && <p className="text-xs text-muted-foreground mt-1">{hint}</p>}
      </CardContent>
    </Card>
  );
}

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
  const hasWinRate = winRate?.win_rate !== null && winRate?.win_rate !== undefined;

  return (
    <main className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          Pequenos jobs freelance em IA, Dados e Programação — ranqueados por IA
        </p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
        <StatCard label="Total de vagas" value={opportunities.length} />
        <StatCard label="APLICAR agora" value={aplicar} accent="green" />
        <StatCard label="AVALIAR" value={avaliar} accent="yellow" />
        <StatCard
          label={quente > 0 ? "🔥 Vagas quentes" : hasWinRate ? "Taxa de ganho" : "Vagas quentes"}
          value={quente > 0 ? quente : hasWinRate ? `${winRate!.win_rate}%` : "—"}
          accent="orange"
          hint={
            winRate && winRate.total > 0 && quente === 0
              ? `${winRate.total} propostas registradas`
              : undefined
          }
        />
      </div>

      {collectError && (
        <div className="mb-4 rounded-xl border border-red-200 bg-red-50 p-4 dark:border-red-500/30 dark:bg-red-500/10">
          <p className="text-sm font-semibold text-red-800 dark:text-red-300 mb-1">
            Falha ao coletar vagas
          </p>
          <p className="text-sm text-red-700 dark:text-red-400 font-mono">{collectError}</p>
          <p className="text-xs text-red-500 mt-1">
            Verifique os logs em: <code>GCP Console → Cloud Run → opportunityai-backend → Logs</code>
          </p>
        </div>
      )}

      <Card>
        <CardContent className="p-6">
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
                <span className="text-xs text-muted-foreground">
                  {lastCollectTime} — {lastCollect.saved} novas · {lastCollect.skipped_duplicate} dup ·{" "}
                  {lastCollect.skipped_fraud} fraude
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
                className="mt-3 text-sm text-primary hover:underline"
              >
                Tentar novamente
              </button>
            </div>
          ) : loading ? (
            <div className="text-center py-16 text-muted-foreground">Carregando vagas…</div>
          ) : (
            <OpportunityTable opportunities={opportunities} />
          )}
        </CardContent>
      </Card>
    </main>
  );
}
