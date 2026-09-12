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
async def test_research_endpoints() -> None:
    async with app.router.lifespan_context(app), AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        status = await client.get("/api/v1/research/status")
        latent = await client.get("/api/v1/research/latent")
        history = await client.get("/api/v1/research/history")
        events = await client.get("/api/v1/research/events")
        resources = await client.get("/api/v1/research/resources")
        agents = await client.get("/api/v1/research/agents")
    assert status.status_code == 200
    assert status.json()["market_training"] is False
    assert status.json()["experiment_id"] is not None
    assert latent.status_code == 200
    assert latent.json()["dimensions"] == 3
    assert isinstance(latent.json()["points"], list)
    assert history.status_code == 200
    assert events.status_code == 200
    assert resources.status_code == 200
    assert resources.json()["worker"] in {"running", "stopped"}
    assert agents.status_code == 200
    assert len(agents.json()) >= 6


@pytest.mark.asyncio
async def test_research_control_rejects_unknown_action() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/research/control?action=unknown")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_latent_dashboard_route() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/research/latent")
    assert response.status_code == 200
    assert "scatter3d" in response.text
    assert "Research Command Center" in response.text
    assert "Experiment history" in response.text
    assert "Guardian status" in response.text
