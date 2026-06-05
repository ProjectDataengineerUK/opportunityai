"use client";

import { useState } from "react";
import { Loader2, RotateCw } from "lucide-react";
import { recalculateOpportunity, Opportunity } from "@/lib/api";
import { Button } from "@/components/ui/button";

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
      <Button variant="outline" size="sm" onClick={handleClick} disabled={loading}>
        {loading ? (
          <>
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            Recalculando…
          </>
        ) : (
          <>
            <RotateCw className="h-3.5 w-3.5" />
            Recalcular Score
          </>
        )}
      </Button>
      {error && <p className="text-xs text-red-500">{error}</p>}
    </div>
  );
}
