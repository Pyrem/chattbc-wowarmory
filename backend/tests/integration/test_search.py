"""Integration tests for search API endpoint."""

from httpx import AsyncClient


async def test_search_requires_query(test_client: AsyncClient) -> None:
    resp = await test_client.get("/api/search")
    assert resp.status_code == 422


async def test_search_too_short(test_client: AsyncClient) -> None:
    resp = await test_client.get("/api/search?q=a")
    assert resp.status_code == 422


async def test_search_returns_empty(test_client: AsyncClient) -> None:
    resp = await test_client.get("/api/search?q=zznonexistent")
    assert resp.status_code == 200
    data = resp.json()
    assert data["results"] == []
    assert data["query"] == "zznonexistent"
    assert data["total"] == 0


async def test_search_invalid_type(test_client: AsyncClient) -> None:
    resp = await test_client.get("/api/search?q=test&type=invalid")
    assert resp.status_code == 422


async def test_search_valid_type_filter(test_client: AsyncClient) -> None:
    resp = await test_client.get("/api/search?q=test&type=character")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["results"], list)
