interface ClientScoreBarProps {
  score: number;
  hireRate: number | null;
  paymentVerified: boolean;
  totalSpent: number | null;
}

export function ClientScoreBar({ score, hireRate, paymentVerified, totalSpent }: ClientScoreBarProps) {
  const color =
    score >= 70 ? "bg-green-500" : score >= 40 ? "bg-yellow-400" : "bg-red-400";

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-3">
        <span className="text-sm text-gray-500 w-36">Score do cliente</span>
        <div className="flex-1 bg-gray-100 rounded-full h-2">
          <div className={`${color} h-2 rounded-full transition-all`} style={{ width: `${score}%` }} />
        </div>
        <span className="text-sm font-mono w-10 text-right">{Math.round(score)}</span>
      </div>

      <div className="flex flex-wrap gap-2 pl-[156px]">
        {paymentVerified && (
          <span className="text-xs bg-green-50 text-green-700 border border-green-200 px-2 py-0.5 rounded-full">
            ✓ Pagamento verificado
          </span>
        )}
        {hireRate !== null && (
          <span className="text-xs bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded-full">
            Taxa de contratação {Math.round(hireRate * 100)}%
          </span>
        )}
        {totalSpent !== null && totalSpent > 0 && (
          <span className="text-xs bg-gray-50 text-gray-600 border border-gray-200 px-2 py-0.5 rounded-full">
            USD {totalSpent.toLocaleString()} gastos
          </span>
        )}
        {!paymentVerified && hireRate === null && totalSpent === null && (
          <span className="text-xs text-gray-400">Dados do cliente indisponíveis nesta plataforma</span>
        )}
      </div>
    </div>
  );
}
