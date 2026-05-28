"use client";

import { useState } from "react";
import { collectOpportunities, CollectResult } from "@/lib/api";

interface CollectButtonProps {
  onComplete: (result: CollectResult) => void;
}

export function CollectButton({ onComplete }: CollectButtonProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleCollect() {
    setLoading(true);
    setError(null);
    try {
      const result = await collectOpportunities();
      onComplete(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao coletar");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex items-center gap-3">
      <button
        onClick={handleCollect}
        disabled={loading}
        className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
      >
        {loading ? (
          <>
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
            Coletando…
          </>
        ) : (
          "Coletar Vagas"
        )}
      </button>
      {error && <span className="text-sm text-red-500">{error}</span>}
    </div>
  );
}
