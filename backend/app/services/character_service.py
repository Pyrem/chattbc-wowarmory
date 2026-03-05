"""Character fetch + cache pipeline.

Flow: check Redis cache -> if hit (fresh), return -> if stale, return
and trigger background refresh -> if miss, fetch from Blizzard, cache,
persist snapshot to DB.
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import BlizzardApiUnavailableError, CharacterNotFoundError
from app.models.character import Character, CharacterSnapshot
from app.services.blizzard import BlizzardClient
from app.services.cache import CHARACTER_TTL, CacheService

logger = structlog.get_logger()

CACHE_KEY_PREFIX = "blizzard:character"


def _cache_key(region: str, realm: str, name: str) -> str:
    return f"{CACHE_KEY_PREFIX}:{region}:{realm.lower()}:{name.lower()}"


class CharacterService:
    def __init__(
        self,
        blizzard: BlizzardClient,
        cache: CacheService,
    ) -> None:
        self.blizzard = blizzard
        self.cache = cache
        self._background_tasks: set[asyncio.Task[None]] = set()

    async def get_character(
        self,
        realm: str,
        name: str,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Fetch character data with stale-while-revalidate caching.

        1. Check Redis cache
        2. If fresh hit -> return immediately
        3. If stale hit -> return immediately, trigger background refresh
        4. If miss -> fetch from Blizzard, cache, persist snapshot, return
        """
        key = _cache_key(self.blizzard.region, realm, name)

        cached = await self.cache.get(key, CHARACTER_TTL)
        if cached is not None:
            data: dict[str, Any] = json.loads(cached.value)
            if cached.is_stale:
                task = asyncio.create_task(self._refresh_character(realm, name, key, db))
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
        """Fetch all character data from Blizzard, cache, and persist."""
        profile = await self.blizzard.get_character(realm, name)

        equipment: dict[str, Any] = {}
        specs: dict[str, Any] = {}
        stats: dict[str, Any] = {}
        pvp: dict[str, Any] = {}
        reps: dict[str, Any] = {}

        # Fetch sub-endpoints in parallel; tolerate individual failures
        results = await asyncio.gather(
            self.blizzard.get_character_equipment(realm, name),
            self.blizzard.get_character_specializations(realm, name),
            self.blizzard.get_character_statistics(realm, name),
            self.blizzard.get_character_pvp_summary(realm, name),
            self.blizzard.get_character_reputations(realm, name),
            return_exceptions=True,
        )

        if not isinstance(results[0], BaseException):
            equipment = results[0]
        if not isinstance(results[1], BaseException):
            specs = results[1]
        if not isinstance(results[2], BaseException):
            stats = results[2]
        if not isinstance(results[3], BaseException):
            pvp = results[3]
        if not isinstance(results[4], BaseException):
            reps = results[4]

        combined: dict[str, Any] = {
            "profile": profile,
            "equipment": equipment,
            "specializations": specs,
            "statistics": stats,
            "pvp": pvp,
            "reputations": reps,
        }

        # Cache the combined result
        await self.cache.set(cache_key, json.dumps(combined), CHARACTER_TTL)

        # Persist to DB
        await self._persist_snapshot(realm, name, profile, combined, db)

        return combined

    async def _refresh_character(
        self,
        realm: str,
        name: str,
        cache_key: str,
        db: AsyncSession,
    ) -> None:
        """Background refresh: fetch fresh data and update cache + DB."""
        try:
            await self._fetch_and_cache(realm, name, cache_key, db)
            logger.info("character_refreshed", realm=realm, name=name)
        except (CharacterNotFoundError, BlizzardApiUnavailableError):
            logger.warning("character_refresh_failed", realm=realm, name=name, exc_info=True)

    async def _persist_snapshot(
        self,
        realm: str,
        name: str,
        profile: dict[str, Any],
        combined: dict[str, Any],
        db: AsyncSession,
    ) -> None:
        """Upsert character record and create a new snapshot."""
        result = await db.execute(
            select(Character).where(
                Character.name == name.lower(),
                Character.realm == realm.lower(),
            )
        )
        character = result.scalar_one_or_none()

        char_class = profile.get("character_class", {}).get("name", "Unknown")
        race = profile.get("race", {}).get("name", "Unknown")
        level = profile.get("level", 0)
        faction = profile.get("faction", {}).get("name", "Unknown")
        guild_name = profile.get("guild", {}).get("name")

        if character is None:
            character = Character(
                name=name.lower(),
                realm=realm.lower(),
                class_=char_class,
                race=race,
                level=level,
                faction=faction,
                guild_name=guild_name,
                last_synced=datetime.now(UTC),
            )
            db.add(character)
            await db.flush()
        else:
            character.class_ = char_class
            character.race = race
            character.level = level
            character.faction = faction
            character.guild_name = guild_name
            character.last_synced = datetime.now(UTC)

        snapshot = CharacterSnapshot(
            character_id=character.id,
            gear_json=combined.get("equipment", {}),
            talents_json=combined.get("specializations", {}),
            stats_json=combined.get("statistics", {}),
            arena_json=combined.get("pvp") or None,
            reputation_json=combined.get("reputations") or None,
        )
        db.add(snapshot)
        await db.commit()
