"""Redis-backed cache with stale-while-revalidate semantics."""

from __future__ import annotations

import time
from dataclasses import dataclass

import structlog
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.config import settings

logger = structlog.get_logger()

# Default TTLs in seconds
CHARACTER_TTL = 2 * 24 * 3600  # 2 days
GUILD_TTL = 2 * 24 * 3600  # 2 days
ITEM_TTL = 30 * 24 * 3600  # 30 days (until patch)
ARENA_TTL = 6 * 3600  # 6 hours


@dataclass(frozen=True)
class CachedValue:
    """A cached value with staleness metadata."""

    value: str
    is_stale: bool


class CacheService:
    """Redis cache with stale-while-revalidate support.

    Each key stores the serialized value. A companion key ``{key}:ts``
    records the Unix timestamp when the value was cached.  Staleness is
    determined by comparing the timestamp against the configured TTL.
    The actual Redis TTL is set to 10x the staleness TTL so stale data
    remains available for serving while a background refresh runs.
    """

    RETENTION_MULTIPLIER = 10

    def __init__(self, redis: Redis | None = None) -> None:
        self._redis = redis

    async def _get_redis(self) -> Redis:
        if self._redis is None:
            self._redis = Redis.from_url(
                settings.redis_url,
                decode_responses=True,
            )
        return self._redis

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None

    async def get(self, key: str, ttl: int) -> CachedValue | None:
        """Retrieve a cached value.

        Returns ``None`` on cache miss or Redis failure.
        ``CachedValue.is_stale`` is ``True`` when the entry is older
        than *ttl* seconds.
        """
        try:
            redis = await self._get_redis()
            pipe = redis.pipeline()
            pipe.get(key)
            pipe.get(f"{key}:ts")
            value, ts_str = await pipe.execute()
        except RedisError:
            logger.warning("cache_get_failed", key=key, exc_info=True)
            return None

        if value is None:
            return None

        is_stale = True
        if ts_str is not None:
            cached_at = float(ts_str)
            is_stale = (time.time() - cached_at) > ttl

        return CachedValue(value=value, is_stale=is_stale)

    async def set(self, key: str, value: str, ttl: int) -> None:
        """Store a value with the given staleness TTL.

        The actual Redis expiry is ``ttl * RETENTION_MULTIPLIER`` so
        stale data can still be served while a background refresh runs.
        """
        try:
            redis = await self._get_redis()
            retention = ttl * self.RETENTION_MULTIPLIER
            pipe = redis.pipeline()
            pipe.set(key, value, ex=retention)
            pipe.set(f"{key}:ts", str(time.time()), ex=retention)
            await pipe.execute()
        except RedisError:
            logger.warning("cache_set_failed", key=key, exc_info=True)

    async def delete(self, key: str) -> None:
        """Remove a key (and its timestamp companion)."""
        try:
            redis = await self._get_redis()
            await redis.delete(key, f"{key}:ts")
        except RedisError:
            logger.warning("cache_delete_failed", key=key, exc_info=True)
