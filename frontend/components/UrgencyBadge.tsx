import { Badge } from "@/components/ui/badge";

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
      <Badge variant="hot">
        🔥 Quente
        {hours !== null && hours < 48 && <span className="opacity-70">{hours}h</span>}
      </Badge>
    );
  }

  if (urgency === "frio") {
    return (
      <Badge variant="muted">
        ❄ Frio
        {proposalsCount !== null && proposalsCount !== undefined && (
          <span className="opacity-70">{proposalsCount} bids</span>
        )}
      </Badge>
    );
  }

  return null;
}
