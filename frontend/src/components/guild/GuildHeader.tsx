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

interface GuildHeaderProps {
  guild: Record<string, unknown>;
  realm: string;
  memberCount: number;
}

export function GuildHeader({ guild, realm, memberCount }: GuildHeaderProps) {
  const name = (guild.name as string) ?? "Unknown Guild";
  const faction = ((guild.faction as Record<string, unknown>) ?? {}).name as
    | string
    | undefined;

  const factionColor = FACTION_COLORS[faction ?? ""] ?? "";

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-3xl">&lt;{name}&gt;</CardTitle>
        <CardDescription>
          <span className={factionColor}>{faction ?? "Unknown"}</span>
          {" — "}
          {realm}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="text-muted-foreground text-sm">
          {memberCount} {memberCount === 1 ? "member" : "members"}
        </div>
      </CardContent>
    </Card>
  );
}
