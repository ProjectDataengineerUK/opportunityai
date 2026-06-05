"use client";

import { useState } from "react";
import { recordOutcome } from "@/lib/api";
import { Button } from "@/components/ui/button";

type Outcome = "ganhou" | "perdeu" | "sem_resposta";

const OPTIONS: { value: Outcome; label: string; variant: "success" | "outline" | "subtle" }[] = [
  { value: "ganhou", label: "Ganhei!", variant: "success" },
  { value: "perdeu", label: "Perdi", variant: "outline" },
  { value: "sem_resposta", label: "Sem resposta", variant: "subtle" },
];

export function OutcomeTracker({ opportunityId }: { opportunityId: string }) {
  const [recorded, setRecorded] = useState<Outcome | null>(null);
  const [loading, setLoading] = useState(false);

  async function handle(outcome: Outcome) {
    setLoading(true);
    try {
      await recordOutcome(opportunityId, outcome);
      setRecorded(outcome);
    } finally {
      setLoading(false);
    }
  }

  if (recorded) {
    const label = OPTIONS.find((o) => o.value === recorded)?.label ?? recorded;
    return (
      <p className="text-sm text-muted-foreground">
        Resultado registrado: <span className="font-medium text-foreground">{label}</span>
      </p>
    );
  }

  return (
    <div className="space-y-2">
      <p className="text-sm font-semibold text-foreground">Qual foi o resultado da sua proposta?</p>
      <div className="flex flex-wrap gap-2">
        {OPTIONS.map((opt) => (
          <Button
            key={opt.value}
            variant={opt.variant}
            size="sm"
            onClick={() => handle(opt.value)}
            disabled={loading}
          >
            {opt.label}
          </Button>
        ))}
      </div>
    </div>
  );
}
