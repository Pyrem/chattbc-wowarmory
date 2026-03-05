import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface RaidBoss {
  name?: string;
  normal_kills?: number;
  heroic_kills?: number;
}

interface RaidInstance {
  name?: string;
  bosses?: RaidBoss[];
}

interface ProgressionData {
  raids?: RaidInstance[];
}

interface GuildProgressionProps {
  progression: Record<string, unknown> | null;
}

export function GuildProgression({ progression }: GuildProgressionProps) {
  const data = progression as unknown as ProgressionData | null;
  const raids = data?.raids ?? [];

  if (raids.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Progression</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-sm">
            No progression data available.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Progression</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {raids.map((raid, idx) => {
            const bosses = raid.bosses ?? [];
            const killed = bosses.filter(
              (b) => (b.normal_kills ?? 0) > 0 || (b.heroic_kills ?? 0) > 0,
            ).length;

            return (
              <div key={idx} className="rounded border p-3">
                <div className="mb-2 flex items-center justify-between">
                  <span className="font-medium">{raid.name ?? "Unknown"}</span>
                  <span className="text-muted-foreground text-sm">
                    {killed}/{bosses.length}
                  </span>
                </div>
                <div className="space-y-1">
                  {bosses.map((boss, bIdx) => {
                    const kills =
                      (boss.normal_kills ?? 0) + (boss.heroic_kills ?? 0);
                    return (
                      <div
                        key={bIdx}
                        className="flex items-center justify-between text-sm"
                      >
                        <span
                          className={
                            kills > 0
                              ? "text-green-500"
                              : "text-muted-foreground"
                          }
                        >
                          {boss.name ?? "Unknown Boss"}
                        </span>
                        <span className="text-muted-foreground text-xs">
                          {kills > 0 ? `${kills} kills` : "—"}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
