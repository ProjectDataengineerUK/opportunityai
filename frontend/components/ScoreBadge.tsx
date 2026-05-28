interface ScoreBadgeProps {
  score: number;
  decision: "APLICAR" | "AVALIAR" | "IGNORAR";
}

const DECISION_STYLES = {
  APLICAR: "bg-green-100 text-green-800 border-green-200",
  AVALIAR: "bg-yellow-100 text-yellow-800 border-yellow-200",
  IGNORAR: "bg-gray-100 text-gray-500 border-gray-200",
};

export function ScoreBadge({ score, decision }: ScoreBadgeProps) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xl font-bold tabular-nums">{Math.round(score)}</span>
      <span
        className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${DECISION_STYLES[decision]}`}
      >
        {decision}
      </span>
    </div>
  );
}
