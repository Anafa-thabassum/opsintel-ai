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
    assert response.headers["X-Request-ID"]
    assert float(response.headers["X-Response-Time-Ms"]) >= 0


def test_incidents_endpoint():
    with patch("app.main.get_failed_pipelines", return_value=SAMPLE_ROWS):
        response = client.get("/incidents")

    assert response.status_code == 200

    data = response.json()
    assert "incidents" in data
    assert data["count"] == len(data["incidents"])


def test_incidents_endpoint_preserves_unknown_row_counts():
    rows = [(7, "metadata_pending", None, None, None, "FAILED", None)]

    with patch("app.main.get_failed_pipelines", return_value=rows):
        response = client.get("/incidents")

    assert response.status_code == 200
    incident = response.json()["incidents"][0]
    assert incident["expected_rows"] is None
    assert incident["actual_rows"] is None
    assert incident["missing_rows"] is None
    assert incident["excess_rows"] is None


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
    with (
        patch(
            "app.main.investigate_pipeline",
            return_value=SAMPLE_INCIDENT.copy(),
        ),
        patch(
            "app.main.summarize_investigation",
            return_value={"status": "disabled"},
        ),
    ):
        response = client.get("/investigate/1")

    assert response.status_code == 200
    assert "root_causes" in response.json()
    assert response.json()["llm_summary"]["status"] == "disabled"


def test_investigation_remains_complete_when_llm_is_unavailable():
    with (
        patch(
            "app.main.investigate_pipeline",
            return_value=SAMPLE_INCIDENT.copy(),
        ),
        patch(
            "app.main.summarize_investigation",
            return_value={"status": "unavailable", "summary": None},
        ),
    ):
        response = client.get("/investigate/1")

    data = response.json()
    assert response.status_code == 200
    assert data["category"] == "incomplete_data"
    assert data["recommended_action"]
    assert data["root_causes"]["confirmed_root_cause"] is None
    assert data["llm_summary"]["status"] == "unavailable"


def test_investigation_api_accepts_unknown_row_counts():
    incident = {
        **SAMPLE_INCIDENT,
        "expected_rows": None,
        "actual_rows": None,
        "missing_rows": None,
        "excess_rows": None,
        "category": "timeout",
        "evidence": [{
            "type": "pipeline_log",
            "observation": "Pipeline execution exceeded the time limit",
            "source": "OPSINTEL.PIPELINE_LOGS",
            "log_id": 8,
        }],
    }

    with (
        patch("app.main.investigate_pipeline", return_value=incident),
        patch(
            "app.main.summarize_investigation",
            return_value={"status": "disabled"},
        ),
    ):
        response = client.get("/investigate/1")

    assert response.status_code == 200
    data = response.json()
    assert data["expected_rows"] is None
    assert data["actual_rows"] is None
    assert data["root_causes"]["confirmed_root_cause"] is None


def test_analytics_trend_endpoint():
    rows = [("2026-10-18", 4, 2, 82.5, 25.0)]

    with patch("app.main.get_pipeline_trend", return_value=rows):
        response = client.get("/analytics/trend")

    assert response.status_code == 200
    assert response.json()["trend"][0]["incident_count"] == 2


def test_analytics_trend_preserves_unknown_completeness():
    rows = [("2026-10-18", 1, 1, None, 100.0)]

    with patch("app.main.get_pipeline_trend", return_value=rows):
        response = client.get("/analytics/trend")

    assert response.status_code == 200
    assert response.json()["trend"][0]["average_completeness_pct"] is None


def test_failure_cascade_endpoint():
    rows = [(
        "customer_sync", 2, "2026-10-19 01:00:00",
        "daily_reporting", 4, "2026-10-19 01:30:00",
        1, " -> daily_reporting", 30,
    )]

    with patch("app.main.get_failure_cascades", return_value=rows):
        response = client.get("/analytics/cascades")

    assert response.status_code == 200
    cascade = response.json()["cascades"][0]
    assert cascade["root_run_id"] == 2
    assert cascade["root_run_time"] == "2026-10-19 01:00:00"
    assert cascade["downstream_pipeline"] == "daily_reporting"
    assert cascade["downstream_run_time"] == "2026-10-19 01:30:00"
    assert cascade["correlation_lag_minutes"] == 30


def test_investigation_returns_503_when_database_fails():
    with patch(
        "app.main.investigate_pipeline",
        side_effect=Exception("Simulated database failure"),
    ):
        response = client.get("/investigate/1")

    assert response.status_code == 503
    assert response.json()["detail"] == "Investigation failed"


def test_analytics_trend_returns_503_when_database_fails():
    with patch(
        "app.main.get_pipeline_trend",
        side_effect=Exception("Simulated database failure"),
    ):
        response = client.get("/analytics/trend")

    assert response.status_code == 503
    assert response.json()["detail"] == "Unable to retrieve pipeline analytics"


def test_failure_cascades_return_503_when_database_fails():
    with patch(
        "app.main.get_failure_cascades",
        side_effect=Exception("Simulated database failure"),
    ):
        response = client.get("/analytics/cascades")

    assert response.status_code == 503
    assert response.json()["detail"] == "Unable to retrieve failure cascades"

