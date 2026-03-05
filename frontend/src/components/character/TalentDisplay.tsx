import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface TalentTree {
  talent_tree?: {
    name?: string;
  };
  specialization_name?: string;
  spent_points?: number;
  talents?: Array<{
    talent?: { name?: string };
    spell_tooltip?: { spell?: { name?: string } };
    rank?: number;
    max_rank?: number;
  }>;
}

interface Specialization {
  specializations?: TalentTree[];
  active_specialization?: {
    name?: string;
  };
}

interface TalentDisplayProps {
  specializations: Record<string, unknown>;
}

export function TalentDisplay({ specializations }: TalentDisplayProps) {
  const specData = specializations as unknown as Specialization;
  const trees = specData?.specializations ?? [];
  const activeSpec = specData?.active_specialization?.name;

  if (trees.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Talents</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-sm">
            No talent data available.
          </p>
        </CardContent>
      </Card>
    );
  }

  // Build summary like "20/41/0"
  const pointsSummary = trees.map((t) => t.spent_points ?? 0).join("/");

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          Talents{" "}
          <span className="text-muted-foreground text-base font-normal">
            ({pointsSummary})
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {trees.map((tree, idx) => {
            const treeName =
              tree.talent_tree?.name ??
              tree.specialization_name ??
              `Tree ${idx + 1}`;
            const points = tree.spent_points ?? 0;
            const isActive = activeSpec === treeName;

            return (
              <div key={idx}>
                <div className="mb-1 flex items-center gap-2">
                  <h3
                    className={`text-sm font-semibold ${isActive ? "text-amber-500" : ""}`}
                  >
                    {treeName}
                  </h3>
                  <span className="text-muted-foreground text-xs">
                    {points} points
                  </span>
                  {isActive && (
                    <span className="rounded bg-amber-500/10 px-1.5 py-0.5 text-xs text-amber-500">
                      Active
                    </span>
                  )}
                </div>
                {tree.talents && tree.talents.length > 0 && (
                  <div className="text-muted-foreground flex flex-wrap gap-1 text-xs">
                    {tree.talents
                      .filter((t) => (t.rank ?? 0) > 0)
                      .map((t, tIdx) => {
                        const name =
                          t.talent?.name ?? t.spell_tooltip?.spell?.name ?? "?";
                        return (
                          <span
                            key={tIdx}
                            className="bg-muted rounded px-1.5 py-0.5"
                            title={`${name} (${t.rank}/${t.max_rank})`}
                          >
                            {name} {t.rank}/{t.max_rank}
                          </span>
                        );
                      })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
