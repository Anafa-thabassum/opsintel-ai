from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)

SAMPLE_ROWS = [(1, "daily_sales_import", 100, 80, 20, "FAILED")]
SAMPLE_INCIDENT = {
    "run_id": 1,
    "pipeline_name": "daily_sales_import",
    "status": "FAILED",
    "expected_rows": 100,
    "actual_rows": 80,
    "missing_rows": 20,
    "category": "incomplete_data",
    "hypothesis": "Fewer rows were received than expected.",
    "confidence": "low",
    "recommended_action": "Inspect source and target counts.",
    "evidence": [],
    "limitations": [],
}


def test_health_endpoint():
    with patch("app.main.check_connection"):
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_incidents_endpoint():
    with patch("app.main.get_failed_pipelines", return_value=SAMPLE_ROWS):
        response = client.get("/incidents")

    assert response.status_code == 200

    data = response.json()
    assert "incidents" in data
    assert data["count"] == len(data["incidents"])


def test_unknown_incident_returns_not_found():
    with patch("app.main.investigate_pipeline", return_value=None):
        response = client.get("/investigate/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Incident not found"


def test_non_integer_run_id_returns_validation_error():
    response = client.get("/investigate/not-a-number")

    assert response.status_code == 422


def test_unknown_run_root_causes_returns_not_found():
    with patch("app.main.investigate_pipeline", return_value=None):
        response = client.get("/investigate/999/root-causes")

    assert response.status_code == 404
    assert response.json()["detail"] == "Incident not found"


def test_health_returns_503_when_database_fails():
    with patch(
        "app.main.check_connection",
        side_effect=Exception("Simulated database failure"),
    ):
        response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["detail"] == "Database connection failed"


def test_incidents_returns_503_when_database_fails():
    with patch(
        "app.main.get_failed_pipelines",
        side_effect=Exception("Simulated database failure"),
    ):
        response = client.get("/incidents")

    assert response.status_code == 503
    assert response.json()["detail"] == "Unable to retrieve incidents"


def test_investigation_includes_root_cause_candidates():
    with patch(
        "app.main.investigate_pipeline",
        return_value=SAMPLE_INCIDENT.copy(),
    ):
        response = client.get("/investigate/1")

    assert response.status_code == 200
    assert "root_causes" in response.json()


def test_analytics_trend_endpoint():
    rows = [("2026-10-18", 4, 2, 82.5, 25.0)]

    with patch("app.main.get_pipeline_trend", return_value=rows):
        response = client.get("/analytics/trend")

    assert response.status_code == 200
    assert response.json()["trend"][0]["incident_count"] == 2

