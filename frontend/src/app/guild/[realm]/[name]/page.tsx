import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { fetchGuild, GuildNotFoundError } from "@/lib/guild-api";
import { GuildHeader } from "@/components/guild/GuildHeader";
import { GuildRoster } from "@/components/guild/GuildRoster";
import { GuildProgression } from "@/components/guild/GuildProgression";

interface PageProps {
  params: Promise<{ realm: string; name: string }>;
}

export async function generateMetadata({
  params,
}: PageProps): Promise<Metadata> {
  const { realm, name } = await params;
  const displayName = decodeURIComponent(name);
  const displayRealm = decodeURIComponent(realm);

  return {
    title: `<${displayName}> - ${displayRealm} | chattbc.gg`,
    description: `View <${displayName}> guild profile on ${displayRealm}. Roster, progression, and more.`,
  };
}

export default async function GuildPage({ params }: PageProps) {
  const { realm, name } = await params;

  let data;
  try {
    data = await fetchGuild(realm, name);
  } catch (err) {
    if (err instanceof GuildNotFoundError) {
      notFound();
    }
    throw err;
  }

  const guild = data.guild as Record<string, unknown>;
  const roster = data.roster as Record<string, unknown>;
  const guildRealm = decodeURIComponent(realm);

  const members = (roster.members ?? []) as unknown[];
  const progression =
    (guild.progression as Record<string, unknown> | null) ?? null;

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <GuildHeader
        guild={guild}
        realm={guildRealm}
        memberCount={members.length}
      />

      <div className="mt-8 grid gap-8 lg:grid-cols-2">
        <GuildRoster roster={roster} realm={guildRealm} />
        <GuildProgression progression={progression} />
      </div>
    </div>
  );
}
