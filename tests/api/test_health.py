import pytest


@pytest.mark.anyio
async def test_health_endpoint_returns_ok(api_client) -> None:
    response = await api_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
