"use client";

import { useState } from "react";
import { Loader2, Download } from "lucide-react";
import { collectOpportunities, CollectResult } from "@/lib/api";
import { Button } from "@/components/ui/button";

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
    <Button onClick={handleCollect} disabled={loading}>
      {loading ? (
        <>
          <Loader2 className="h-4 w-4 animate-spin" />
          Coletando…
        </>
      ) : (
        <>
          <Download className="h-4 w-4" />
          Coletar Vagas
        </>
      )}
    </Button>
  );
}
