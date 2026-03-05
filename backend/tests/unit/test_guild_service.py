"""Unit tests for GuildService — cache hit, miss, stale refresh."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from app.services.cache import CachedValue
from app.services.guild_service import GuildService

SAMPLE_GUILD = {
    "name": "Nihilum",
    "faction": {"name": "Horde"},
    "member_count": 50,
}

SAMPLE_ROSTER = {
    "members": [{"character": {"name": "Player1"}}, {"character": {"name": "Player2"}}],
}

SAMPLE_COMBINED = {
    "guild": SAMPLE_GUILD,
    "roster": SAMPLE_ROSTER,
}


@pytest.fixture
def mock_blizzard() -> AsyncMock:
    blizzard = AsyncMock()
    blizzard.region = "us"
    blizzard.get_guild = AsyncMock(return_value=SAMPLE_GUILD)
    blizzard.get_guild_roster = AsyncMock(return_value=SAMPLE_ROSTER)
    return blizzard


@pytest.fixture
def mock_cache() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_db() -> AsyncMock:
    db = AsyncMock()
    result_mock = AsyncMock()
    result_mock.scalar_one_or_none = lambda: None
    db.execute = AsyncMock(return_value=result_mock)
    db.commit = AsyncMock()
    return db


@pytest.fixture
def service(mock_blizzard: AsyncMock, mock_cache: AsyncMock) -> GuildService:
    return GuildService(blizzard=mock_blizzard, cache=mock_cache)


class TestGuildCacheMiss:
    async def test_fetches_from_blizzard_on_miss(
        self,
        service: GuildService,
        mock_blizzard: AsyncMock,
        mock_cache: AsyncMock,
        mock_db: AsyncMock,
    ) -> None:
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()

        result = await service.get_guild("Faerlina", "Nihilum", mock_db)

        mock_blizzard.get_guild.assert_called_once_with("Faerlina", "Nihilum")
        mock_cache.set.assert_called_once()
        assert result["guild"]["name"] == "Nihilum"


class TestGuildCacheHitFresh:
    async def test_returns_cached_data(
        self,
        service: GuildService,
        mock_blizzard: AsyncMock,
        mock_cache: AsyncMock,
        mock_db: AsyncMock,
    ) -> None:
        cached = CachedValue(value=json.dumps(SAMPLE_COMBINED), is_stale=False)
        mock_cache.get = AsyncMock(return_value=cached)

        result = await service.get_guild("Faerlina", "Nihilum", mock_db)

        mock_blizzard.get_guild.assert_not_called()
        assert result["guild"]["name"] == "Nihilum"


class TestGuildCacheHitStale:
    async def test_returns_stale_and_triggers_refresh(
        self,
        service: GuildService,
        mock_blizzard: AsyncMock,
        mock_cache: AsyncMock,
        mock_db: AsyncMock,
    ) -> None:
        cached = CachedValue(value=json.dumps(SAMPLE_COMBINED), is_stale=True)
        mock_cache.get = AsyncMock(return_value=cached)
        mock_cache.set = AsyncMock()

        with patch("app.services.guild_service.asyncio") as mock_asyncio:
            mock_task = AsyncMock()
            mock_task.add_done_callback = lambda _cb: None
            mock_asyncio.create_task = lambda coro: (coro.close(), mock_task)[1]

            result = await service.get_guild("Faerlina", "Nihilum", mock_db)

        assert result["guild"]["name"] == "Nihilum"
        mock_blizzard.get_guild.assert_not_called()
