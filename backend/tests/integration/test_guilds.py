"""Integration tests for guild API endpoints."""

from unittest.mock import AsyncMock

from httpx import AsyncClient

from app.dependencies import get_guild_service
from app.exceptions import GuildNotFoundError
from app.main import app
from app.services.guild_service import GuildService

SAMPLE_DATA = {
    "guild": {
        "name": "Risen",
        "faction": {"name": "Horde"},
        "realm": {"name": "Faerlina"},
    },
    "roster": {
        "members": [
            {
                "character": {"name": "Testchar", "level": 70},
                "rank": 0,
            },
        ],
    },
}


async def test_get_guild_success(test_client: AsyncClient) -> None:
    mock_service = AsyncMock(spec=GuildService)
    mock_service.get_guild = AsyncMock(return_value=SAMPLE_DATA)
    app.dependency_overrides[get_guild_service] = lambda: mock_service

    resp = await test_client.get("/api/guilds/faerlina/risen")

    assert resp.status_code == 200
    data = resp.json()
    assert data["guild"]["name"] == "Risen"
    assert len(data["roster"]["members"]) == 1

    del app.dependency_overrides[get_guild_service]


async def test_get_guild_not_found(test_client: AsyncClient) -> None:
    mock_service = AsyncMock(spec=GuildService)
    mock_service.get_guild = AsyncMock(side_effect=GuildNotFoundError("faerlina", "noguild"))
    app.dependency_overrides[get_guild_service] = lambda: mock_service

    resp = await test_client.get("/api/guilds/faerlina/noguild")

    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()

    del app.dependency_overrides[get_guild_service]
