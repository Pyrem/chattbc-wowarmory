"""Integration tests for Battle.net linking endpoints."""

from unittest.mock import MagicMock

from httpx import AsyncClient

from app.dependencies import get_current_user
from app.main import app


def _mock_user(user_id: int = 1, bnet_id: int | None = None) -> MagicMock:
    user = MagicMock()
    user.id = user_id
    user.email = "test@example.com"
    user.display_name = "Tester"
    user.email_verified = True
    user.battle_net_id = bnet_id
    user.battletag = "Player#1234" if bnet_id else None
    return user


async def test_authorize_requires_auth(test_client: AsyncClient) -> None:
    resp = await test_client.get("/api/auth/bnet/authorize")
    assert resp.status_code in (401, 403)


async def test_authorize_returns_url(test_client: AsyncClient) -> None:
    user = _mock_user()
    app.dependency_overrides[get_current_user] = lambda: user

    resp = await test_client.get("/api/auth/bnet/authorize")
    assert resp.status_code == 200
    data = resp.json()
    assert "authorize_url" in data
    assert "oauth.battle.net" in data["authorize_url"]
    assert "state" in data

    del app.dependency_overrides[get_current_user]


async def test_unlink_requires_auth(test_client: AsyncClient) -> None:
    resp = await test_client.delete("/api/auth/bnet/unlink")
    assert resp.status_code in (401, 403)


async def test_unlink_no_linked_account(test_client: AsyncClient) -> None:
    user = _mock_user(bnet_id=None)
    app.dependency_overrides[get_current_user] = lambda: user

    resp = await test_client.delete("/api/auth/bnet/unlink")
    assert resp.status_code == 400

    del app.dependency_overrides[get_current_user]


async def test_linked_characters_requires_auth(test_client: AsyncClient) -> None:
    resp = await test_client.get("/api/auth/bnet/characters")
    assert resp.status_code in (401, 403)


async def test_callback_invalid_state(test_client: AsyncClient) -> None:
    resp = await test_client.get("/api/auth/bnet/callback?code=test&state=invalid")
    assert resp.status_code == 400
