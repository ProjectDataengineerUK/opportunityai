interface UrgencyBadgeProps {
  urgency: "quente" | "normal" | "frio";
  proposalsCount?: number | null;
  postedAt?: string | null;
}

function hoursAgo(dateStr: string | null | undefined): number | null {
  if (!dateStr) return null;
  const diff = Date.now() - new Date(dateStr).getTime();
  return Math.floor(diff / 3_600_000);
}

export function UrgencyBadge({ urgency, proposalsCount, postedAt }: UrgencyBadgeProps) {
  const hours = hoursAgo(postedAt);

  if (urgency === "quente") {
    return (
      <span className="inline-flex items-center gap-1 text-xs font-medium bg-orange-50 text-orange-700 border border-orange-200 px-2 py-0.5 rounded-full">
        🔥 Quente
        {hours !== null && hours < 48 && <span className="text-orange-400">{hours}h</span>}
      </span>
    );
  }

  if (urgency === "frio") {
    return (
      <span className="inline-flex items-center gap-1 text-xs font-medium bg-gray-50 text-gray-500 border border-gray-200 px-2 py-0.5 rounded-full">
        ❄ Frio
        {proposalsCount !== null && proposalsCount !== undefined && (
          <span className="text-gray-400">{proposalsCount} bids</span>
        )}
      </span>
    );
  }

  return null;
}
