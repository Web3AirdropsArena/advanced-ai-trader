from fastapi.testclient import TestClient

from app.api import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_system_is_not_live_by_default() -> None:
    response = client.get("/api/v1/system")
    assert response.status_code == 200
    assert response.json()["live_execution"] == "disabled_until_explicit_enablement"
