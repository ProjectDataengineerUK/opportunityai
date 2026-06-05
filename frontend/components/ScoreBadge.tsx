import { Badge } from "@/components/ui/badge";

interface ScoreBadgeProps {
  score: number;
  decision: "APLICAR" | "AVALIAR" | "IGNORAR";
}

const DECISION_VARIANT = {
  APLICAR: "success",
  AVALIAR: "warning",
  IGNORAR: "muted",
} as const;

export function ScoreBadge({ score, decision }: ScoreBadgeProps) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xl font-bold tabular-nums">{Math.round(score)}</span>
      <Badge variant={DECISION_VARIANT[decision]}>{decision}</Badge>
    </div>
  );
}
