
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
