"""Unit tests for BlizzardClient — token refresh, retry, error mapping."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.exceptions import (
    BlizzardApiUnavailableError,
    CharacterNotFoundError,
    GuildNotFoundError,
)
from app.services.blizzard import BlizzardClient


def _token_response(expires_in: int = 86400) -> httpx.Response:
    return httpx.Response(
        200,
        json={"access_token": "test-token", "expires_in": expires_in},
        request=httpx.Request("POST", "https://oauth.battle.net/token"),
    )


def _api_response(status: int, body: dict | None = None) -> httpx.Response:
    return httpx.Response(
        status,
        json=body or {},
        request=httpx.Request("GET", "https://us.api.blizzard.com/test"),
    )


@pytest.fixture
def client() -> BlizzardClient:
    return BlizzardClient(
        client_id="test-id",
        client_secret="test-secret",
        region="us",
    )


class TestTokenRefresh:
    async def test_fetches_token_on_first_request(self, client: BlizzardClient) -> None:
        mock_http = AsyncMock()
        mock_http.is_closed = False
        mock_http.post = AsyncMock(return_value=_token_response())
        mock_http.request = AsyncMock(return_value=_api_response(200, {"name": "Arthas"}))

        client._http = mock_http
        result = await client.get_character("Faerlina", "Arthas")

        mock_http.post.assert_called_once()
        assert result["name"] == "Arthas"

    async def test_reuses_cached_token(self, client: BlizzardClient) -> None:
        mock_http = AsyncMock()
        mock_http.is_closed = False
        mock_http.post = AsyncMock(return_value=_token_response())
        mock_http.request = AsyncMock(return_value=_api_response(200, {"name": "X"}))

        client._http = mock_http
        await client.get_character("Faerlina", "A")
        await client.get_character("Faerlina", "B")

        # Token endpoint called only once
        assert mock_http.post.call_count == 1

    async def test_refreshes_token_on_401(self, client: BlizzardClient) -> None:
        mock_http = AsyncMock()
        mock_http.is_closed = False
        mock_http.post = AsyncMock(return_value=_token_response())
        mock_http.request = AsyncMock(
            side_effect=[
                _api_response(401),
                _api_response(200, {"name": "Refreshed"}),
            ]
        )

        client._http = mock_http
        result = await client.get_character("Faerlina", "Test")

        # Token refreshed after 401
        assert mock_http.post.call_count == 2
        assert result["name"] == "Refreshed"


class TestRetryBehavior:
    async def test_retries_on_429(self, client: BlizzardClient) -> None:
        mock_http = AsyncMock()
        mock_http.is_closed = False
        mock_http.post = AsyncMock(return_value=_token_response())
        mock_http.request = AsyncMock(
            side_effect=[
                _api_response(429),
                _api_response(200, {"name": "Success"}),
            ]
        )

        client._http = mock_http
        with patch("app.services.blizzard.BlizzardClient._backoff", new_callable=AsyncMock):
            result = await client.get_character("Faerlina", "Test")

        assert result["name"] == "Success"

    async def test_retries_on_500(self, client: BlizzardClient) -> None:
        mock_http = AsyncMock()
        mock_http.is_closed = False
        mock_http.post = AsyncMock(return_value=_token_response())
        mock_http.request = AsyncMock(
            side_effect=[
                _api_response(500),
                _api_response(200, {"name": "Recovered"}),
            ]
        )

        client._http = mock_http
        with patch("app.services.blizzard.BlizzardClient._backoff", new_callable=AsyncMock):
            result = await client.get_character("Faerlina", "Test")

        assert result["name"] == "Recovered"

    async def test_raises_after_max_retries(self, client: BlizzardClient) -> None:
        mock_http = AsyncMock()
        mock_http.is_closed = False
        mock_http.post = AsyncMock(return_value=_token_response())
        mock_http.request = AsyncMock(return_value=_api_response(500))

        client._http = mock_http
        with (
            patch("app.services.blizzard.BlizzardClient._backoff", new_callable=AsyncMock),
            pytest.raises(BlizzardApiUnavailableError),
        ):
            await client.get_character("Faerlina", "Test")

    async def test_uses_retry_after_header(self, client: BlizzardClient) -> None:
        resp_429 = httpx.Response(
            429,
            json={},
            headers={"Retry-After": "0.01"},
            request=httpx.Request("GET", "https://us.api.blizzard.com/test"),
        )
        mock_http = AsyncMock()
        mock_http.is_closed = False
        mock_http.post = AsyncMock(return_value=_token_response())
        mock_http.request = AsyncMock(side_effect=[resp_429, _api_response(200, {"ok": True})])

        client._http = mock_http
        result = await client.get_character("Faerlina", "Test")
        assert result["ok"] is True


class TestErrorMapping:
    async def test_404_raises_character_not_found(self, client: BlizzardClient) -> None:
        mock_http = AsyncMock()
        mock_http.is_closed = False
        mock_http.post = AsyncMock(return_value=_token_response())
        mock_http.request = AsyncMock(return_value=_api_response(404))

        client._http = mock_http
        with pytest.raises(CharacterNotFoundError):
            await client.get_character("Faerlina", "Nobody")

    async def test_404_raises_guild_not_found(self, client: BlizzardClient) -> None:
        mock_http = AsyncMock()
        mock_http.is_closed = False
        mock_http.post = AsyncMock(return_value=_token_response())
        mock_http.request = AsyncMock(return_value=_api_response(404))

        client._http = mock_http
        with pytest.raises(GuildNotFoundError):
            await client.get_guild("Faerlina", "NoGuild")

    async def test_network_error_raises_unavailable(self, client: BlizzardClient) -> None:
        mock_http = AsyncMock()
        mock_http.is_closed = False
        mock_http.post = AsyncMock(return_value=_token_response())
        mock_http.request = AsyncMock(side_effect=httpx.ConnectError("fail"))

        client._http = mock_http
        with (
            patch("app.services.blizzard.BlizzardClient._backoff", new_callable=AsyncMock),
            pytest.raises(BlizzardApiUnavailableError),
        ):
            await client.get_character("Faerlina", "Test")


class TestSlugify:
    async def test_realm_slugified(self, client: BlizzardClient) -> None:
        mock_http = AsyncMock()
        mock_http.is_closed = False
        mock_http.post = AsyncMock(return_value=_token_response())
        mock_http.request = AsyncMock(return_value=_api_response(200, {"ok": True}))

        client._http = mock_http
        await client.get_character("Burning Blade", "Test")

        call_args = mock_http.request.call_args
        url = call_args[1].get("url") or call_args[0][1]
        assert "burning-blade" in str(url)
