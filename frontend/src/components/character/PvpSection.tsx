import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface ArenaBracket {
  rating?: number;
  season_match_statistics?: {
    played?: number;
    won?: number;
    lost?: number;
  };
  weekly_match_statistics?: {
    played?: number;
    won?: number;
    lost?: number;
  };
  team?: { name?: string };
}

interface PvpData {
  brackets?: Record<string, ArenaBracket>;
  honorable_kills?: number;
  honor_level?: number;
  pvp_map_statistics?: unknown[];
}

interface PvpSectionProps {
  pvp: Record<string, unknown>;
}

const BRACKET_LABELS: Record<string, string> = {
  ARENA_BRACKET_2v2: "2v2 Arena",
  ARENA_BRACKET_3v3: "3v3 Arena",
  ARENA_BRACKET_5v5: "5v5 Arena",
  "2v2": "2v2 Arena",
  "3v3": "3v3 Arena",
  "5v5": "5v5 Arena",
};

export function PvpSection({ pvp }: PvpSectionProps) {
  const pvpData = pvp as unknown as PvpData;
  const brackets = pvpData?.brackets ?? {};
  const hks = pvpData?.honorable_kills;

  const hasBrackets = Object.keys(brackets).length > 0;
  const hasData = hasBrackets || hks !== undefined;

  return (
    <Card>
      <CardHeader>
        <CardTitle>PvP & Arena</CardTitle>
      </CardHeader>
      <CardContent>
        {!hasData ? (
          <p className="text-muted-foreground text-sm">
            No PvP data available.
          </p>
        ) : (
          <div className="space-y-4">
            {hks !== undefined && (
              <div>
                <span className="text-muted-foreground text-sm">
                  Honorable Kills:
                </span>{" "}
                <span className="font-semibold">{hks.toLocaleString()}</span>
              </div>
            )}

            {hasBrackets && (
              <div className="space-y-3">
                {Object.entries(brackets).map(([key, bracket]) => (
                  <BracketRow
                    key={key}
                    label={BRACKET_LABELS[key] ?? key}
                    bracket={bracket}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function BracketRow({
  label,
  bracket,
}: {
  label: string;
  bracket: ArenaBracket;
}) {
  const rating = bracket.rating ?? 0;
  const season = bracket.season_match_statistics;
  const team = bracket.team?.name;

  return (
    <div className="rounded border p-3">
      <div className="mb-1 flex items-center justify-between">
        <span className="text-sm font-medium">{label}</span>
        <span className="text-lg font-bold">{rating}</span>
      </div>
      {team && (
        <div className="text-muted-foreground text-xs">Team: {team}</div>
      )}
      {season && (
        <div className="text-muted-foreground text-xs">
          Season: {season.won ?? 0}W - {season.lost ?? 0}L
          {season.played ? ` (${season.played} played)` : ""}
        </div>
      )}
    </div>
  );
}
