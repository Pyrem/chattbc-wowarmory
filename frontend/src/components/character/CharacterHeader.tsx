import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const FACTION_COLORS: Record<string, string> = {
  Alliance: "text-blue-600",
  Horde: "text-red-600",
};

interface CharacterHeaderProps {
  profile: Record<string, unknown>;
  realm: string;
}

export function CharacterHeader({ profile, realm }: CharacterHeaderProps) {
  const name = (profile.name as string) ?? "Unknown";
  const level = (profile.level as number) ?? 0;
  const charClass = ((profile.character_class as Record<string, unknown>) ?? {})
    .name as string | undefined;
  const race = ((profile.race as Record<string, unknown>) ?? {}).name as
    | string
    | undefined;
  const faction = ((profile.faction as Record<string, unknown>) ?? {}).name as
    | string
    | undefined;
  const guild = ((profile.guild as Record<string, unknown>) ?? {}).name as
    | string
    | undefined;

  const factionColor = FACTION_COLORS[faction ?? ""] ?? "";

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-3xl">{name}</CardTitle>
        <CardDescription>
          Level {level} {race} {charClass} &mdash;{" "}
          <span className={factionColor}>{faction ?? "Unknown"}</span>
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-4 text-sm">
          <div>
            <span className="text-muted-foreground">Realm:</span>{" "}
            <span className="font-medium">{realm}</span>
          </div>
          {guild && (
            <div>
              <span className="text-muted-foreground">Guild:</span>{" "}
              <span className="font-medium">&lt;{guild}&gt;</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
