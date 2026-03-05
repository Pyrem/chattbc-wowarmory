"""Unit tests for CacheService — hit, miss, stale, Redis down."""

import time
from unittest.mock import AsyncMock

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError

from app.services.cache import CacheService


@pytest.fixture
def mock_redis() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def cache(mock_redis: AsyncMock) -> CacheService:
    svc = CacheService(redis=mock_redis)
    return svc


class TestCacheGet:
    async def test_cache_miss_returns_none(
        self, cache: CacheService, mock_redis: AsyncMock
    ) -> None:
        pipe = AsyncMock()
        pipe.get = AsyncMock()
        pipe.execute = AsyncMock(return_value=[None, None])
        mock_redis.pipeline = lambda: pipe

        result = await cache.get("some:key", ttl=3600)
        assert result is None

    async def test_cache_hit_fresh(self, cache: CacheService, mock_redis: AsyncMock) -> None:
        now = str(time.time())
        pipe = AsyncMock()
        pipe.get = AsyncMock()
        pipe.execute = AsyncMock(return_value=['{"name":"Arthas"}', now])
        mock_redis.pipeline = lambda: pipe

        result = await cache.get("some:key", ttl=3600)
        assert result is not None
        assert result.value == '{"name":"Arthas"}'
        assert result.is_stale is False

    async def test_cache_hit_stale(self, cache: CacheService, mock_redis: AsyncMock) -> None:
        old_ts = str(time.time() - 7200)  # 2 hours ago
        pipe = AsyncMock()
        pipe.get = AsyncMock()
        pipe.execute = AsyncMock(return_value=['{"name":"Arthas"}', old_ts])
        mock_redis.pipeline = lambda: pipe

        result = await cache.get("some:key", ttl=3600)
        assert result is not None
        assert result.is_stale is True

    async def test_redis_down_returns_none(self, cache: CacheService) -> None:
        broken_redis = AsyncMock()
        pipe = AsyncMock()
        pipe.get = AsyncMock()
        pipe.execute = AsyncMock(side_effect=RedisConnectionError("down"))
        broken_redis.pipeline = lambda: pipe
        cache._redis = broken_redis

        result = await cache.get("some:key", ttl=3600)
        assert result is None


class TestCacheSet:
    async def test_sets_value_with_retention(
        self, cache: CacheService, mock_redis: AsyncMock
    ) -> None:
        pipe = AsyncMock()
        pipe.set = AsyncMock()
        pipe.execute = AsyncMock(return_value=[True, True])
        mock_redis.pipeline = lambda: pipe

        await cache.set("some:key", '{"data":1}', ttl=3600)

        # Should be called twice: once for value, once for timestamp
        assert pipe.set.call_count == 2
        # Retention should be ttl * RETENTION_MULTIPLIER
        first_call = pipe.set.call_args_list[0]
        assert first_call[1].get("ex") == 3600 * CacheService.RETENTION_MULTIPLIER

    async def test_redis_down_on_set_does_not_raise(self, cache: CacheService) -> None:
        broken_redis = AsyncMock()
        pipe = AsyncMock()
        pipe.set = AsyncMock()
        pipe.execute = AsyncMock(side_effect=RedisConnectionError("down"))
        broken_redis.pipeline = lambda: pipe
        cache._redis = broken_redis

        # Should not raise
        await cache.set("some:key", "value", ttl=3600)


class TestCacheDelete:
    async def test_deletes_key_and_timestamp(
        self, cache: CacheService, mock_redis: AsyncMock
    ) -> None:
        await cache.delete("some:key")
        mock_redis.delete.assert_called_once_with("some:key", "some:key:ts")

    async def test_redis_down_on_delete_does_not_raise(self, cache: CacheService) -> None:
        broken_redis = AsyncMock()
        broken_redis.delete = AsyncMock(side_effect=RedisConnectionError("down"))
        cache._redis = broken_redis

        # Should not raise
        await cache.delete("some:key")
