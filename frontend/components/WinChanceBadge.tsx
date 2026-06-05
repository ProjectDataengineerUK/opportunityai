interface WinChanceBadgeProps {
  probability: number | null;
}

export function WinChanceBadge({ probability }: WinChanceBadgeProps) {
  if (probability == null) return <span className="text-muted-foreground/50">—</span>;

  const pct = Math.round(probability * 100);
  const color =
    pct >= 65
      ? "text-green-600 dark:text-green-400"
      : pct >= 45
      ? "text-yellow-600 dark:text-yellow-400"
      : "text-muted-foreground";

  return (
    <span
      className={`text-xs font-semibold tabular-nums ${color}`}
      title="Chance estimada de fechar, baseada no histórico de desfechos"
    >
      {pct}%
    </span>
  );
}
