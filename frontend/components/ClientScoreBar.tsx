import { Badge } from "@/components/ui/badge";

interface ClientScoreBarProps {
  score: number;
  hireRate: number | null;
  paymentVerified: boolean;
  totalSpent: number | null;
}

export function ClientScoreBar({ score, hireRate, paymentVerified, totalSpent }: ClientScoreBarProps) {
  const color = score >= 70 ? "bg-green-500" : score >= 40 ? "bg-yellow-400" : "bg-red-400";

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-3">
        <span className="text-sm text-muted-foreground w-36">Score do cliente</span>
        <div className="flex-1 bg-muted rounded-full h-2">
          <div className={`${color} h-2 rounded-full transition-all`} style={{ width: `${score}%` }} />
        </div>
        <span className="text-sm font-mono w-10 text-right">{Math.round(score)}</span>
      </div>

      <div className="flex flex-wrap gap-2 pl-[156px]">
        {paymentVerified && <Badge variant="success">✓ Pagamento verificado</Badge>}
        {hireRate !== null && (
          <Badge variant="info">Taxa de contratação {Math.round(hireRate * 100)}%</Badge>
        )}
        {totalSpent !== null && totalSpent > 0 && (
          <Badge variant="muted">USD {totalSpent.toLocaleString()} gastos</Badge>
        )}
        {!paymentVerified && hireRate === null && totalSpent === null && (
          <span className="text-xs text-muted-foreground">
            Dados do cliente indisponíveis nesta plataforma
          </span>
        )}
      </div>
    </div>
  );
}
