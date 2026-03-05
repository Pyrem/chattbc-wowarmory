import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { fetchCharacter, CharacterNotFoundError } from "@/lib/character-api";
import { CharacterHeader } from "@/components/character/CharacterHeader";
import { VerifiedBadge } from "@/components/character/VerifiedBadge";
import { GearDisplay } from "@/components/character/GearDisplay";
import { TalentDisplay } from "@/components/character/TalentDisplay";
import { PvpSection } from "@/components/character/PvpSection";
import { ReputationDisplay } from "@/components/character/ReputationDisplay";

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
    title: `${displayName} - ${displayRealm} | chattbc.gg`,
    description: `View ${displayName}'s character profile on ${displayRealm}. Gear, talents, arena ratings, and more.`,
  };
}

export default async function CharacterPage({ params }: PageProps) {
  const { realm, name } = await params;

  let data;
  try {
    data = await fetchCharacter(realm, name);
  } catch (err) {
    if (err instanceof CharacterNotFoundError) {
      notFound();
    }
    throw err;
  }

  const profile = data.profile as Record<string, unknown>;
  const charRealm = decodeURIComponent(realm);

  const SERVER_API_BASE =
    process.env.INTERNAL_API_URL ??
    process.env.NEXT_PUBLIC_API_URL ??
    "http://localhost:8000";
  let verified = false;
  try {
    const ownerRes = await fetch(
      `${SERVER_API_BASE}/api/characters/${encodeURIComponent(realm)}/${encodeURIComponent(name)}/owner`,
      { next: { revalidate: 60 } },
    );
    if (ownerRes.ok) {
      const ownerData = (await ownerRes.json()) as { verified: boolean };
      verified = ownerData.verified;
    }
  } catch {
    // Owner check failed — just don't show badge
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <div className="flex items-center gap-3">
        <CharacterHeader profile={profile} realm={charRealm} />
      </div>
      {verified && (
        <div className="mt-2">
          <VerifiedBadge />
        </div>
      )}

      <div className="mt-8 grid gap-8 lg:grid-cols-2">
        <GearDisplay equipment={data.equipment} />
        <TalentDisplay specializations={data.specializations} />
      </div>

      <div className="mt-8 grid gap-8 lg:grid-cols-2">
        <PvpSection pvp={data.pvp} />
        <ReputationDisplay reputations={data.reputations} />
      </div>
    </div>
  );
}
