"""Integration tests for realms API endpoint."""

from httpx import AsyncClient


async def test_list_realms(test_client: AsyncClient) -> None:
    resp = await test_client.get("/api/realms")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    first = data[0]
    assert "slug" in first
    assert "name" in first
    assert "type" in first
    assert "region" in first
    assert "population" in first
