"""Unit tests for CharacterService — cache hit, miss, stale refresh."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from app.services.cache import CachedValue
from app.services.character_service import CharacterService

SAMPLE_PROFILE = {
    "name": "Arthas",
    "level": 70,
    "character_class": {"name": "Paladin"},
    "race": {"name": "Human"},
    "faction": {"name": "Alliance"},
    "guild": {"name": "Knights of the Silver Hand"},
}

SAMPLE_COMBINED = {
    "profile": SAMPLE_PROFILE,
    "equipment": {"items": []},
    "specializations": {"trees": []},
    "statistics": {"stats": {}},
    "pvp": {"ratings": {}},
    "reputations": {"factions": []},
}


@pytest.fixture
def mock_blizzard() -> AsyncMock:
    blizzard = AsyncMock()
    blizzard.region = "us"
    blizzard.get_character = AsyncMock(return_value=SAMPLE_PROFILE)
    blizzard.get_character_equipment = AsyncMock(return_value={"items": []})
    blizzard.get_character_specializations = AsyncMock(return_value={"trees": []})
    blizzard.get_character_statistics = AsyncMock(return_value={"stats": {}})
    blizzard.get_character_pvp_summary = AsyncMock(return_value={"ratings": {}})
    blizzard.get_character_reputations = AsyncMock(return_value={"factions": []})
    return blizzard


@pytest.fixture
def mock_cache() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_db() -> AsyncMock:
    db = AsyncMock()
    # Simulate no existing character in DB
    result_mock = AsyncMock()
    result_mock.scalar_one_or_none = lambda: None
    db.execute = AsyncMock(return_value=result_mock)
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    return db


@pytest.fixture
def service(mock_blizzard: AsyncMock, mock_cache: AsyncMock) -> CharacterService:
    return CharacterService(blizzard=mock_blizzard, cache=mock_cache)


class TestCacheMiss:
    async def test_fetches_from_blizzard_on_miss(
        self,
        service: CharacterService,
        mock_blizzard: AsyncMock,
        mock_cache: AsyncMock,
        mock_db: AsyncMock,
    ) -> None:
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()

        result = await service.get_character("Faerlina", "Arthas", mock_db)

        mock_blizzard.get_character.assert_called_once_with("Faerlina", "Arthas")
        mock_cache.set.assert_called_once()
        assert result["profile"]["name"] == "Arthas"


class TestCacheHitFresh:
    async def test_returns_cached_data(
        self,
        service: CharacterService,
        mock_blizzard: AsyncMock,
        mock_cache: AsyncMock,
        mock_db: AsyncMock,
    ) -> None:
        cached = CachedValue(value=json.dumps(SAMPLE_COMBINED), is_stale=False)
        mock_cache.get = AsyncMock(return_value=cached)

        result = await service.get_character("Faerlina", "Arthas", mock_db)

        # Should NOT call Blizzard API
        mock_blizzard.get_character.assert_not_called()
        assert result["profile"]["name"] == "Arthas"


class TestCacheHitStale:
    async def test_returns_stale_and_triggers_refresh(
        self,
        service: CharacterService,
        mock_blizzard: AsyncMock,
        mock_cache: AsyncMock,
        mock_db: AsyncMock,
    ) -> None:
        cached = CachedValue(value=json.dumps(SAMPLE_COMBINED), is_stale=True)
        mock_cache.get = AsyncMock(return_value=cached)
        mock_cache.set = AsyncMock()

        with patch("app.services.character_service.asyncio") as mock_asyncio:
            mock_task = AsyncMock()
            mock_task.add_done_callback = lambda _cb: None
            mock_asyncio.create_task = lambda coro: (coro.close(), mock_task)[1]
            mock_asyncio.gather = AsyncMock(
                return_value=[
                    {"items": []},
                    {"trees": []},
                    {"stats": {}},
                    {"ratings": {}},
                    {"factions": []},
                ]
            )

            result = await service.get_character("Faerlina", "Arthas", mock_db)

        # Returns cached data immediately
        assert result["profile"]["name"] == "Arthas"
        # Should NOT have awaited Blizzard directly (background task)
        mock_blizzard.get_character.assert_not_called()
