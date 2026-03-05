"""Blizzard Developer API client using Client Credentials OAuth."""

import asyncio
import time
from typing import Any

import httpx
import structlog

from app.config import settings
from app.exceptions import (
    BlizzardApiUnavailableError,
    CharacterNotFoundError,
    GuildNotFoundError,
)

logger = structlog.get_logger()

# Retry configuration
MAX_RETRIES = 3
BACKOFF_BASE = 1.0  # seconds
BACKOFF_MAX = 10.0  # seconds

# Jitter factor for exponential backoff (0.0-1.0)
JITTER_FACTOR = 0.5


class BlizzardClient:
    """Async Blizzard API client with Client Credentials auth and retry."""

    def __init__(
        self,
        client_id: str = "",
        client_secret: str = "",
        region: str = "us",
    ) -> None:
        self.client_id = client_id or settings.blizzard_client_id
        self.client_secret = client_secret or settings.blizzard_client_secret
        self.region = region or settings.blizzard_region
        self.base_url = f"https://{self.region}.api.blizzard.com"
        self.token_url = "https://oauth.battle.net/token"
        self._token: str | None = None
        self._token_expires: float = 0.0
        self._http: httpx.AsyncClient | None = None

    async def _get_http(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(timeout=httpx.Timeout(30.0))
        return self._http

    async def close(self) -> None:
        if self._http is not None and not self._http.is_closed:
            await self._http.aclose()
            self._http = None

    async def _ensure_token(self) -> str:
        """Fetch or refresh the Client Credentials token."""
        if self._token and time.time() < self._token_expires - 60:
            return self._token

        http = await self._get_http()
        response = await http.post(
            self.token_url,
            data={"grant_type": "client_credentials"},
            auth=(self.client_id, self.client_secret),
        )
        response.raise_for_status()
        data = response.json()

        token: str = data["access_token"]
        self._token = token
        # expires_in is in seconds; subtract buffer for safety
        self._token_expires = time.time() + data.get("expires_in", 86400)
        logger.info("blizzard_token_refreshed", expires_in=data.get("expires_in"))
        return token

    def _invalidate_token(self) -> None:
        """Force token refresh on next request."""
        self._token = None
        self._token_expires = 0.0

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Make an authenticated request with retry and backoff.

        Retries on 429 (rate limited) and 5xx (server error).
        On 401, refreshes token and retries once.
        """
        last_exc: Exception | None = None

        for attempt in range(MAX_RETRIES + 1):
            token = await self._ensure_token()
            http = await self._get_http()

            merged_params = {"namespace": f"profile-classic-{self.region}", "locale": "en_US"}
            if params:
                merged_params.update(params)

            try:
                response = await http.request(
                    method,
                    f"{self.base_url}{path}",
                    headers={"Authorization": f"Bearer {token}"},
                    params=merged_params,
                )
            except httpx.HTTPError as exc:
                last_exc = exc
                if attempt < MAX_RETRIES:
                    await self._backoff(attempt)
                    continue
                raise BlizzardApiUnavailableError(
                    f"Network error after {MAX_RETRIES + 1} attempts"
                ) from exc

            # Log rate limit headers if present
            quota_remaining = response.headers.get("X-Plan-Quota-Remaining")
            if quota_remaining is not None:
                logger.debug(
                    "blizzard_quota",
                    remaining=quota_remaining,
                    path=path,
                )

            if response.status_code == 200:
                return response.json()  # type: ignore[no-any-return]

            if response.status_code == 401 and attempt == 0:
                # Token expired — refresh and retry once
                self._invalidate_token()
                continue

            if response.status_code == 404:
                # Let caller handle 404 mapping
                raise _NotFoundError(path)

            if response.status_code == 429 or response.status_code >= 500:
                last_exc = BlizzardApiUnavailableError(
                    f"HTTP {response.status_code} from Blizzard API: {path}"
                )
                if attempt < MAX_RETRIES:
                    retry_after = response.headers.get("Retry-After")
                    if retry_after:
                        await asyncio.sleep(float(retry_after))
                    else:
                        await self._backoff(attempt)
                    continue

            # Unexpected status code
            raise BlizzardApiUnavailableError(
                f"Unexpected HTTP {response.status_code} from Blizzard API: {path}"
            )

        raise BlizzardApiUnavailableError(
            f"Blizzard API request failed after {MAX_RETRIES + 1} attempts"
        ) from last_exc

    @staticmethod
    async def _backoff(attempt: int) -> None:
        """Exponential backoff with jitter."""
        import random

        delay = min(BACKOFF_BASE * (2**attempt), BACKOFF_MAX)
        jitter = delay * JITTER_FACTOR * random.random()  # noqa: S311
        await asyncio.sleep(delay + jitter)

    # ── Public API ──────────────────────────────────────────────

    async def get_character(self, realm: str, name: str) -> dict[str, Any]:
        """Fetch character profile from Blizzard API.

        Raises CharacterNotFoundError on 404.
        """
        slug = _slugify(realm)
        lower_name = name.lower()
        try:
            return await self._request("GET", f"/profile/wow/character/{slug}/{lower_name}")
        except _NotFoundError as exc:
            raise CharacterNotFoundError(realm, name) from exc

    async def get_character_equipment(self, realm: str, name: str) -> dict[str, Any]:
        """Fetch character equipment."""
        slug = _slugify(realm)
        lower_name = name.lower()
        try:
            return await self._request(
                "GET", f"/profile/wow/character/{slug}/{lower_name}/equipment"
            )
        except _NotFoundError as exc:
            raise CharacterNotFoundError(realm, name) from exc

    async def get_character_specializations(self, realm: str, name: str) -> dict[str, Any]:
        """Fetch character talent specializations."""
        slug = _slugify(realm)
        lower_name = name.lower()
        try:
            return await self._request(
                "GET", f"/profile/wow/character/{slug}/{lower_name}/specializations"
            )
        except _NotFoundError as exc:
            raise CharacterNotFoundError(realm, name) from exc

    async def get_character_statistics(self, realm: str, name: str) -> dict[str, Any]:
        """Fetch character statistics."""
        slug = _slugify(realm)
        lower_name = name.lower()
        try:
            return await self._request(
                "GET", f"/profile/wow/character/{slug}/{lower_name}/statistics"
            )
        except _NotFoundError as exc:
            raise CharacterNotFoundError(realm, name) from exc

    async def get_character_pvp_summary(self, realm: str, name: str) -> dict[str, Any]:
        """Fetch character PvP summary (arena ratings, HKs)."""
        slug = _slugify(realm)
        lower_name = name.lower()
        try:
            return await self._request(
                "GET", f"/profile/wow/character/{slug}/{lower_name}/pvp-summary"
            )
        except _NotFoundError as exc:
            raise CharacterNotFoundError(realm, name) from exc

    async def get_character_reputations(self, realm: str, name: str) -> dict[str, Any]:
        """Fetch character reputation standings."""
        slug = _slugify(realm)
        lower_name = name.lower()
        try:
            return await self._request(
                "GET", f"/profile/wow/character/{slug}/{lower_name}/reputations"
            )
        except _NotFoundError as exc:
            raise CharacterNotFoundError(realm, name) from exc

    async def get_guild(self, realm: str, name: str) -> dict[str, Any]:
        """Fetch guild info. Raises GuildNotFoundError on 404."""
        slug = _slugify(realm)
        lower_name = name.lower()
        try:
            return await self._request(
                "GET",
                f"/data/wow/guild/{slug}/{lower_name}",
                params={"namespace": f"profile-classic-{self.region}"},
            )
        except _NotFoundError as exc:
            raise GuildNotFoundError(realm, name) from exc

    async def get_guild_roster(self, realm: str, name: str) -> dict[str, Any]:
        """Fetch guild roster."""
        slug = _slugify(realm)
        lower_name = name.lower()
        try:
            return await self._request(
                "GET",
                f"/data/wow/guild/{slug}/{lower_name}/roster",
                params={"namespace": f"profile-classic-{self.region}"},
            )
        except _NotFoundError as exc:
            raise GuildNotFoundError(realm, name) from exc


class _NotFoundError(Exception):
    """Internal sentinel for 404 responses."""

    def __init__(self, path: str) -> None:
        self.path = path
        super().__init__(f"404 Not Found: {path}")


def _slugify(realm: str) -> str:
    """Convert a realm name to a URL slug (e.g. 'Burning Blade' → 'burning-blade')."""
    return realm.lower().replace(" ", "-").replace("'", "")
