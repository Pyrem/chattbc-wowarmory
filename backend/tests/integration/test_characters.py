"""Integration tests for character API endpoints."""

from unittest.mock import AsyncMock

from httpx import AsyncClient

from app.dependencies import get_character_service
from app.exceptions import CharacterNotFoundError
from app.main import app
from app.services.character_service import CharacterService

SAMPLE_DATA = {
    "profile": {
        "name": "Arthas",
        "level": 70,
        "character_class": {"name": "Paladin"},
        "race": {"name": "Human"},
        "faction": {"name": "Alliance"},
    },
    "equipment": {"items": []},
    "specializations": {"trees": []},
    "statistics": {"stats": {}},
    "pvp": {},
    "reputations": {},
}


async def test_get_character_success(test_client: AsyncClient) -> None:
    mock_service = AsyncMock(spec=CharacterService)
    mock_service.get_character = AsyncMock(return_value=SAMPLE_DATA)
    app.dependency_overrides[get_character_service] = lambda: mock_service

    resp = await test_client.get("/api/characters/faerlina/arthas")

    assert resp.status_code == 200
    data = resp.json()
    assert data["profile"]["name"] == "Arthas"
    assert data["profile"]["level"] == 70
    assert "equipment" in data
    assert "specializations" in data

    del app.dependency_overrides[get_character_service]


async def test_get_character_not_found(test_client: AsyncClient) -> None:
    mock_service = AsyncMock(spec=CharacterService)
    mock_service.get_character = AsyncMock(
        side_effect=CharacterNotFoundError("faerlina", "nobody")
    )
    app.dependency_overrides[get_character_service] = lambda: mock_service

    resp = await test_client.get("/api/characters/faerlina/nobody")

    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()

    del app.dependency_overrides[get_character_service]
