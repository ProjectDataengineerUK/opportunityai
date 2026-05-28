"use client";

import { useState } from "react";
import { recalculateOpportunity, Opportunity } from "@/lib/api";

interface Props {
  id: string;
  onComplete: (updated: Opportunity) => void;
}

export function RecalculateButton({ id, onComplete }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleClick() {
    setLoading(true);
    setError(null);
    try {
      const updated = await recalculateOpportunity(id);
      onComplete(updated);
    } catch {
      setError("Falha ao recalcular. Tente novamente.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <button
        onClick={handleClick}
        disabled={loading}
        className="inline-flex items-center gap-2 border border-gray-300 hover:border-gray-400 text-gray-700 text-sm font-medium px-4 py-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? (
          <>
            <span className="inline-block h-3.5 w-3.5 rounded-full border-2 border-gray-400 border-t-transparent animate-spin" />
            Recalculando…
          </>
        ) : (
          "↻ Recalcular Score"
        )}
      </button>
      {error && <p className="text-xs text-red-500">{error}</p>}
    </div>
  );
}
