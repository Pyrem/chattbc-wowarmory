from httpx import AsyncClient


async def test_health_returns_200(test_client: AsyncClient) -> None:
    resp = await test_client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["app_name"] == "chattbc"
