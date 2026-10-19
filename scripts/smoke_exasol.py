"""Exercise the live Exasol-backed API with the seeded demonstration data."""

import json

from fastapi.testclient import TestClient

from app.main import app


def main():
    client = TestClient(app)
    health = client.get("/health")
    incidents = client.get("/incidents")
    investigation = client.get("/investigate/1")
    cascades = client.get("/analytics/cascades")

    for response in (health, incidents, investigation, cascades):
        response.raise_for_status()

    result = investigation.json()
    comparison = result["comparison"]
    cascade_rows = cascades.json()["cascades"]
    assert result["category"] == "early_termination"
    assert result["root_causes"]["confirmed_root_cause"] is None
    assert comparison["status"] == "available"
    assert comparison["last_successful_run"]["run_id"] == 113
    assert comparison["new_or_changed_logs"]
    assert cascade_rows
    assert all(
        0 <= item["correlation_lag_minutes"] <= 120
        for item in cascade_rows
    )

    print(json.dumps({
        "health": health.json()["status"],
        "incident_count": incidents.json()["count"],
        "investigated_run": result["run_id"],
        "classification": result["category"],
        "last_successful_run": comparison["last_successful_run"]["run_id"],
        "new_or_changed_logs": len(comparison["new_or_changed_logs"]),
        "candidate_count": len(result["root_causes"]["candidates"]),
        "confirmed_root_cause": result["root_causes"]["confirmed_root_cause"],
        "llm_status": result["llm_summary"]["status"],
        "cascade_count": len(cascade_rows),
    }, indent=2))


if __name__ == "__main__":
    main()
