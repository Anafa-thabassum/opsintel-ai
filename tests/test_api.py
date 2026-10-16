from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_incidents_endpoint():
    response = client.get("/incidents")

    assert response.status_code == 200

    data = response.json()
    assert "incidents" in data
    assert data["count"] == len(data["incidents"])


def test_unknown_incident_returns_not_found():
    response = client.get("/investigate/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Incident not found"

def test_non_integer_run_id_returns_validation_error():
    response = client.get("/investigate/not-a-number")

    assert response.status_code == 422


def test_unknown_run_root_causes_returns_not_found():
    response = client.get("/investigate/999/root-causes")

    assert response.status_code == 404
    assert response.json()["detail"] == "Incident not found"
def test_health_returns_503_when_database_fails():
    with patch(
        "app.main.get_failed_pipelines",
        side_effect=Exception("Simulated database failure"),
    ):
        response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["detail"] == "Database connection failed"

