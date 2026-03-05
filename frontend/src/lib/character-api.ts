/** Server-side fetch — no auth needed for public armory data. */
const SERVER_API_BASE =
  process.env.INTERNAL_API_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000";

export interface CharacterData {
  profile: Record<string, unknown>;
  equipment: Record<string, unknown>;
  specializations: Record<string, unknown>;
  statistics: Record<string, unknown>;
  pvp: Record<string, unknown>;
  reputations: Record<string, unknown>;
}

export async function fetchCharacter(
  realm: string,
  name: string,
): Promise<CharacterData> {
  const res = await fetch(
    `${SERVER_API_BASE}/api/characters/${encodeURIComponent(realm)}/${encodeURIComponent(name)}`,
    { next: { revalidate: 300 } },
  );

  if (!res.ok) {
    if (res.status === 404) {
      throw new CharacterNotFoundError(realm, name);
    }
    throw new Error(`Failed to fetch character: ${res.status}`);
  }

  return res.json() as Promise<CharacterData>;
}

export class CharacterNotFoundError extends Error {
  constructor(
    public realm: string,
    public characterName: string,
  ) {
    super(`Character ${characterName} on ${realm} not found`);
    this.name = "CharacterNotFoundError";
  }
}
