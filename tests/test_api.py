import pytest
from httpx import ASGITransport, AsyncClient

from app.api import app


@pytest.mark.asyncio
async def test_health() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_system_is_not_live_by_default() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/system")
    assert response.status_code == 200
    assert response.json()["live_execution"] == "disabled_until_explicit_enablement"


@pytest.mark.asyncio
async def test_research_status_endpoint() -> None:
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/research/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"training", "completed"}
    assert payload["market_training"] is False
    assert payload["experiment_id"] is not None


@pytest.mark.asyncio
async def test_research_latent_endpoint() -> None:
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/research/latent")
    assert response.status_code == 200
    payload = response.json()
    assert payload["dimensions"] == 3
    assert isinstance(payload["points"], list)


@pytest.mark.asyncio
async def test_latent_dashboard_route() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/research/latent")
    assert response.status_code == 200
    assert "scatter3d" in response.text
