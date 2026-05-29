"use client";

import { useState } from "react";
import { collectOpportunities, CollectResult } from "@/lib/api";

interface CollectButtonProps {
  onComplete: (result: CollectResult) => void;
  onError?: (message: string) => void;
}

export function CollectButton({ onComplete, onError }: CollectButtonProps) {
  const [loading, setLoading] = useState(false);

  async function handleCollect() {
    setLoading(true);
    try {
      const result = await collectOpportunities();
      onComplete(result);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Erro ao coletar";
      onError?.(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
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
  );
}
