# Blizzard API Integration

## Two Separate API Clients

### 1. Developer API Client (Client Credentials)
- **Purpose:** Fetch all armory data — characters, guilds, arena ladders, items, quests.
- **Auth flow:** Client Credentials grant. Server-side only.
- **Token management:** Fetch token on startup, cache it, auto-refresh before expiry.
- **Rate limits:** 36,000 requests/hour per client. Monitor via response headers.
- **Implementation:** `app/services/blizzard.py` → `BlizzardClient` class.

### 2. OAuth Client (Authorization Code)
- **Purpose:** Prove character ownership when a user opts to link their Battle.net account.
- **Auth flow:** Authorization Code grant. Confidential client (secret stays server-side).
- **Scope:** `wow.profile` — access to the user's character list.
- **Implementation:** `app/services/bnet_linking.py` → handles redirect, callback, token exchange.
- **Important:** Blizzard does NOT support PKCE or public clients. The client secret MUST stay server-side.

## BlizzardClient Implementation

```python
# app/services/blizzard.py
class BlizzardClient:
    """Server-side Blizzard API client using Client Credentials."""

    def __init__(self, client_id: str, client_secret: str, region: str = "us"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.region = region
        self.base_url = f"https://{region}.api.blizzard.com"
        self.token_url = "https://oauth.battle.net/token"
        self._token: str | None = None
        self._token_expires: float = 0

    async def _ensure_token(self) -> str:
        """Fetch or refresh the Client Credentials token."""
        if self._token and time.time() < self._token_expires - 60:
            return self._token
        # Fetch new token...

    async def get_character(self, realm: str, name: str) -> CharacterData:
        """Fetch character profile. Raises CharacterNotFoundError on 404."""

    async def get_guild(self, realm: str, name: str) -> GuildData:
        """Fetch guild roster and info."""

    async def get_arena_ladder(self, bracket: str, season: int) -> list[ArenaEntry]:
        """Fetch arena ladder snapshot."""
```

## API Endpoints Used

### Character Data
- `GET /profile/wow/character/{realm}/{name}` — Basic profile
- `GET /profile/wow/character/{realm}/{name}/equipment` — Equipped gear
- `GET /profile/wow/character/{realm}/{name}/specializations` — Talent spec
- `GET /profile/wow/character/{realm}/{name}/statistics` — Character stats
- `GET /profile/wow/character/{realm}/{name}/pvp-summary` — Arena/PvP data
- `GET /profile/wow/character/{realm}/{name}/reputations` — Faction standings
- `GET /profile/wow/character/{realm}/{name}/quests/completed` — For attunement tracking

### Guild Data
- `GET /data/wow/guild/{realm}/{name}` — Guild info
- `GET /data/wow/guild/{realm}/{name}/roster` — Member list

### Arena
- `GET /data/wow/pvp-season/{season}/pvp-leaderboard/{bracket}` — Ladder snapshot

### Static Game Data
- `GET /data/wow/item/{id}` — Item details
- `GET /data/wow/spell/{id}` — Spell/ability details

**NOTE:** These endpoints may differ for Classic/TBC APIs vs retail. An API audit (script: `scripts/blizzard_audit.py`) must be run before Phase 1 development to confirm which endpoints are available and their response shapes.

## Caching Strategy

### Cache Key Format
```
blizzard:character:{region}:{realm}:{name}
blizzard:guild:{region}:{realm}:{name}
blizzard:arena:{region}:{season}:{bracket}
blizzard:item:{id}
```

### Stale-While-Revalidate Flow
```python
async def get_character_cached(self, realm: str, name: str) -> CharacterData:
    cache_key = f"blizzard:character:{self.region}:{realm}:{name}"

    # 1. Check cache
    cached = await self.cache.get(cache_key)
    if cached:
        data = CharacterData.model_validate_json(cached.value)
        # 2. If stale, trigger background refresh (don't wait)
        if cached.is_stale:
            asyncio.create_task(self._refresh_character(realm, name, cache_key))
        return data

    # 3. Cache miss — fetch from Blizzard, cache, persist snapshot
    data = await self.blizzard.get_character(realm, name)
    await self.cache.set(cache_key, data.model_dump_json(), ttl=CHARACTER_TTL)
    await self._persist_snapshot(realm, name, data)
    return data
```

### Rate Limit Handling
- Monitor `X-Plan-Quota-Remaining` response header.
- On 429 Too Many Requests: exponential backoff with jitter. Max 3 retries.
- Log rate limit events to track usage patterns.
- If quota is consistently near limit: increase cache TTLs or reduce background refresh frequency.

## Error Mapping

| Blizzard Status | Our Response | Notes |
|----------------|-------------|-------|
| 200 | Return data | |
| 404 | `CharacterNotFoundError` / `GuildNotFoundError` | Character may not exist or be below level threshold |
| 401 | Retry with fresh token | Token expired |
| 429 | Backoff + retry | Rate limited |
| 500, 502, 503 | `BlizzardApiUnavailableError` | Serve stale cache if available |
