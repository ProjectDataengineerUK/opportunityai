"use client";

import { useState } from "react";
import { recordOutcome } from "@/lib/api";

type Outcome = "ganhou" | "perdeu" | "sem_resposta";

const OPTIONS: { value: Outcome; label: string; style: string }[] = [
  { value: "ganhou", label: "Ganhei!", style: "bg-green-600 hover:bg-green-700 text-white" },
  { value: "perdeu", label: "Perdi", style: "bg-red-100 hover:bg-red-200 text-red-700 border border-red-200" },
  { value: "sem_resposta", label: "Sem resposta", style: "bg-gray-100 hover:bg-gray-200 text-gray-600 border border-gray-200" },
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
      <p className="text-sm text-gray-500">
        Resultado registrado: <span className="font-medium text-gray-700">{label}</span>
      </p>
    );
  }

  return (
    <div className="space-y-2">
      <p className="text-sm font-semibold text-gray-700">Qual foi o resultado da sua proposta?</p>
      <div className="flex flex-wrap gap-2">
        {OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => handle(opt.value)}
            disabled={loading}
            className={`text-sm font-medium px-4 py-2 rounded-lg transition-colors disabled:opacity-50 ${opt.style}`}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}
