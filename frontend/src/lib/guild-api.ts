/** Server-side fetch for guild data. */
const SERVER_API_BASE =
  process.env.INTERNAL_API_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000";

export interface GuildData {
  guild: Record<string, unknown>;
  roster: Record<string, unknown>;
}

export async function fetchGuild(
  realm: string,
  name: string,
): Promise<GuildData> {
  const res = await fetch(
    `${SERVER_API_BASE}/api/guilds/${encodeURIComponent(realm)}/${encodeURIComponent(name)}`,
    { next: { revalidate: 300 } },
  );

  if (!res.ok) {
    if (res.status === 404) {
      throw new GuildNotFoundError(realm, name);
    }
    throw new Error(`Failed to fetch guild: ${res.status}`);
  }

  return res.json() as Promise<GuildData>;
}

export class GuildNotFoundError extends Error {
  constructor(
    public realm: string,
    public guildName: string,
  ) {
    super(`Guild ${guildName} on ${realm} not found`);
    this.name = "GuildNotFoundError";
  }
}
