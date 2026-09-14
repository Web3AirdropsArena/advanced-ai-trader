import pytest
from httpx import ASGITransport, AsyncClient

from app.api import app
from research.latent_supervisor import LatentResearchSupervisor, RESEARCH_PHASES


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
    assert response.json()["web_dashboard"] == "disabled_during_research"


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
    body = status.json()
    assert body["market_training"] is False
    assert body["experiment_id"] is not None
    assert body["stage_one_complete"] is False
    assert body["next_stage_ready"] is False
    assert 0.0 <= body["research_progress"] <= 15.0
    assert body["program_stage_index"] == 1
    assert body["program_stage_count"] == len(RESEARCH_PHASES)
    assert body["program_stage_name"] == RESEARCH_PHASES[0][0]
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
async def test_latent_dashboard_is_disabled_during_research() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/research/latent")
    assert response.status_code == 404


def test_stage_one_completion_requires_evidence(tmp_path) -> None:
    supervisor = LatentResearchSupervisor(tmp_path / "status.json")
    with pytest.raises(ValueError):
        supervisor.mark_stage_one_complete(" ")


def test_stage_one_completion_publishes_stage_two_signal(tmp_path) -> None:
    supervisor = LatentResearchSupervisor(tmp_path / "status.json")
    supervisor.mark_stage_one_complete("validated walk-forward evidence")
    status = supervisor.status()
    assert status["stage_one_complete"] is True
    assert status["next_stage_ready"] is True
    assert status["stage"] == "stage_1_complete"
    assert status["progress"] == 100.0
    assert status["research_progress"] == RESEARCH_PHASES[0][1]
    assert "STAGE 1 COMPLETE" in status["message"]


def test_research_progress_is_stage_weighted(tmp_path) -> None:
    supervisor = LatentResearchSupervisor(tmp_path / "status.json")
    supervisor._set(stage="stage_1_research_training", progress=50.0)
    status = supervisor.status()
    assert status["research_progress"] == RESEARCH_PHASES[0][1] / 2
    assert status["program_stage_index"] == 1
