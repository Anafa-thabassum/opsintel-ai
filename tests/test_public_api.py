"""Public routes preserve read-only behavior and safe database failures."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_public_search_forwards_bounded_filters():
    with patch("app.main.public_data.list_public_incidents", return_value={"total": 0, "incidents": []}) as search:
        response = client.get("/public/incidents?source=apache/airflow&category=timeout&search=DagBag&limit=5&offset=2")
    assert response.status_code == 200
    assert response.json() == {"total": 0, "incidents": []}
    search.assert_called_once_with(source="apache/airflow", category="timeout", search="DagBag", limit=5, offset=2)
    assert client.get("/public/incidents?limit=0").status_code == 422


def test_public_detail_returns_404_for_missing_record():
    with patch("app.main.public_data.get_public_incident", return_value=None):
        response = client.get("/public/incidents/apache/airflow/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Public incident not found"


def test_public_db_failure_hides_internal_exception():
    with patch("app.main.public_data.public_analytics", side_effect=RuntimeError("db password in private error")):
        response = client.get("/public/analytics")
    assert response.status_code == 503
    assert "db password" not in response.text
