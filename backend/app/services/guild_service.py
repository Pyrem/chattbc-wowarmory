"""Guild fetch + cache pipeline.

Same stale-while-revalidate pattern as character_service.
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import BlizzardApiUnavailableError, GuildNotFoundError
from app.models.guild import Guild
from app.services.blizzard import BlizzardClient
from app.services.cache import GUILD_TTL, CacheService

logger = structlog.get_logger()

CACHE_KEY_PREFIX = "blizzard:guild"


def _cache_key(region: str, realm: str, name: str) -> str:
    return f"{CACHE_KEY_PREFIX}:{region}:{realm.lower()}:{name.lower()}"


class GuildService:
    def __init__(
        self,
        blizzard: BlizzardClient,
        cache: CacheService,
    ) -> None:
        self.blizzard = blizzard
        self.cache = cache
        self._background_tasks: set[asyncio.Task[None]] = set()

    async def get_guild(
        self,
        realm: str,
        name: str,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Fetch guild data with stale-while-revalidate caching."""
        key = _cache_key(self.blizzard.region, realm, name)

        cached = await self.cache.get(key, GUILD_TTL)
        if cached is not None:
            data: dict[str, Any] = json.loads(cached.value)
            if cached.is_stale:
                task = asyncio.create_task(self._refresh_guild(realm, name, key, db))
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)
            return data

        return await self._fetch_and_cache(realm, name, key, db)

    async def _fetch_and_cache(
        self,
        realm: str,
        name: str,
        cache_key: str,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Fetch guild + roster from Blizzard, cache, persist."""
        guild_info = await self.blizzard.get_guild(realm, name)

        roster: dict[str, Any] = {}
        try:
            roster = await self.blizzard.get_guild_roster(realm, name)
        except (GuildNotFoundError, BlizzardApiUnavailableError):
            logger.warning("guild_roster_fetch_failed", realm=realm, name=name)

        combined: dict[str, Any] = {
            "guild": guild_info,
            "roster": roster,
        }

        await self.cache.set(cache_key, json.dumps(combined), GUILD_TTL)
        await self._persist_guild(realm, name, guild_info, roster, db)

        return combined

    async def _refresh_guild(
        self,
        realm: str,
        name: str,
        cache_key: str,
        db: AsyncSession,
    ) -> None:
        """Background refresh for stale guild data."""
        try:
            await self._fetch_and_cache(realm, name, cache_key, db)
            logger.info("guild_refreshed", realm=realm, name=name)
        except (GuildNotFoundError, BlizzardApiUnavailableError):
            logger.warning("guild_refresh_failed", realm=realm, name=name, exc_info=True)

    async def _persist_guild(
        self,
        realm: str,
        name: str,
        guild_info: dict[str, Any],
        roster: dict[str, Any],
        db: AsyncSession,
    ) -> None:
        """Upsert guild record in the database."""
        result = await db.execute(
            select(Guild).where(
                Guild.name == name.lower(),
                Guild.realm == realm.lower(),
            )
        )
        guild = result.scalar_one_or_none()

        faction = guild_info.get("faction", {}).get("name", "Unknown")
        member_count = roster.get("members")
        if isinstance(member_count, list):
            member_count = len(member_count)

        if guild is None:
            guild = Guild(
                name=name.lower(),
                realm=realm.lower(),
                faction=faction,
                member_count=member_count,
                progression_json=None,
                last_synced=datetime.now(UTC),
            )
            db.add(guild)
        else:
            guild.faction = faction
            guild.member_count = member_count
            guild.last_synced = datetime.now(UTC)

        await db.commit()
