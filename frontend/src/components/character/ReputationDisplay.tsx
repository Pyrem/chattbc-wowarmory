import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface ReputationFaction {
  faction?: { name?: string };
  standing?: {
    name?: string;
    raw?: number;
    max?: number;
    value?: number;
    tier?: number;
  };
}

interface ReputationsData {
  reputations?: ReputationFaction[];
}

const STANDING_COLORS: Record<string, string> = {
  Hated: "bg-red-700",
  Hostile: "bg-red-600",
  Unfriendly: "bg-orange-600",
  Neutral: "bg-yellow-600",
  Friendly: "bg-green-600",
  Honored: "bg-green-500",
  Revered: "bg-blue-500",
  Exalted: "bg-purple-500",
};

interface ReputationDisplayProps {
  reputations: Record<string, unknown>;
}

export function ReputationDisplay({ reputations }: ReputationDisplayProps) {
  const repData = reputations as unknown as ReputationsData;
  const factions = repData?.reputations ?? [];

  if (factions.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Reputations</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-sm">
            No reputation data available.
          </p>
        </CardContent>
      </Card>
    );
  }

  // Sort by standing tier descending (Exalted first)
  const sorted = [...factions].sort((a, b) => {
    const tierA = a.standing?.tier ?? 0;
    const tierB = b.standing?.tier ?? 0;
    return tierB - tierA;
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          Reputations{" "}
          <span className="text-muted-foreground text-base font-normal">
            ({factions.length})
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {sorted.map((rep, idx) => (
            <ReputationRow key={idx} rep={rep} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function ReputationRow({ rep }: { rep: ReputationFaction }) {
  const name = rep.faction?.name ?? "Unknown";
  const standing = rep.standing?.name ?? "Neutral";
  const value = rep.standing?.value ?? 0;
  const max = rep.standing?.max ?? 1;
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0;
  const barColor = STANDING_COLORS[standing] ?? "bg-gray-500";

  return (
    <div>
      <div className="mb-0.5 flex items-center justify-between text-sm">
        <span className="truncate font-medium">{name}</span>
        <span className="text-muted-foreground shrink-0 text-xs">
          {standing}{" "}
          {standing !== "Exalted" && (
            <span>
              ({value}/{max})
            </span>
          )}
        </span>
      </div>
      <div className="bg-muted h-1.5 w-full overflow-hidden rounded-full">
        <div
          className={`h-full rounded-full transition-all ${barColor}`}
          style={{ width: `${standing === "Exalted" ? 100 : pct}%` }}
        />
      </div>
    </div>
  );
}
