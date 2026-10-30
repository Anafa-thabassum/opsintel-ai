"""Public issue provenance and Exasol boundary checks; no live API in CI."""

import pytest
from urllib.error import HTTPError

from app import public_data
from scripts.migrate_database import MIGRATIONS
from scripts.setup_database import load_statements


SOURCE = public_data.source_registry()["sources"][0]
ISSUE = {
    "number": 46378,
    "html_url": "https://github.com/apache/airflow/issues/46378",
    "title": "Airflow on k8s: DagBag import timeout",
    "body": "The task did not complete.\nAirflowTaskTimeout: DagBag import timeout\ncontact me@example.com",
    "state": "closed", "created_at": "2025-02-03T14:38:58Z",
    "updated_at": "2025-02-05T18:53:49Z",
}


def test_normalization_retains_source_and_supports_abstention():
    item = public_data.normalize_issue(ISSUE, SOURCE, collected_at="2026-10-31T00:00:00Z",
                                       project_label="timeout")
    assert item["source_key"] == "apache/airflow#46378"
    assert item["source_url"] == ISSUE["html_url"]
    assert item["excerpt"] == "AirflowTaskTimeout: DagBag import timeout"
    assert item["excerpt_origin"] == "body-line-2"
    assert item["classifier_category"] == "timeout"
    assert item["classification"]["confirmed_root_cause"] is None
    assert item["label_status"] == "project_assigned_unreviewed"
    assert "me@example.com" not in str(item)


def test_rejects_wrong_identity_and_pull_requests():
    with pytest.raises(ValueError, match="source identity"):
        public_data.normalize_issue({**ISSUE, "html_url": "https://evil.example/46378"}, SOURCE)
    with pytest.raises(ValueError, match="source identity"):
        public_data.normalize_issue({**ISSUE, "pull_request": {}}, SOURCE)


class _Result:
    def __init__(self, row):
        self.row = row

    def fetchone(self):
        return self.row


class _Connection:
    def __init__(self, row=None):
        self.row = row
        self.writes = []

    def execute(self, query, params=None):
        if query.strip().startswith("SELECT"):
            return _Result(self.row)
        self.writes.append((query, params))


def test_ingestion_is_idempotent_and_uses_bound_values():
    item = public_data.normalize_issue(ISSUE, SOURCE)
    first = _Connection()
    assert public_data.ingest_issue(first, item) == "inserted"
    assert "{title}" in first.writes[0][0]
    assert first.writes[0][1]["title"] == ISSUE["title"]
    unchanged = _Connection((item["body_sha256"], item["source_updated_at"],
                             item["excerpt"], item["excerpt_origin"], item["classifier_category"]))
    assert public_data.ingest_issue(unchanged, item) == "unchanged"
    assert unchanged.writes == []


def test_public_migration_is_additive():
    statements = load_statements(MIGRATIONS / "002_public_incidents.sql")
    assert len(statements) == 1
    assert statements[0].startswith("CREATE TABLE IF NOT EXISTS OPSINTEL.PUBLIC_INCIDENTS")
    assert "DROP" not in statements[0]


def test_project_labels_resolve_canonical_dbt_repository():
    labels = public_data._project_labels()
    assert labels["apache/airflow#46378"] == "timeout"
    assert labels["dbt-labs/dbt#15914"] == "unclassified"


def test_rate_limit_error_explains_recovery():
    def limited(_request, timeout):
        assert timeout == 15
        raise HTTPError("https://api.github.com", 403, "rate limited",
                        {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1793392420"}, None)

    with pytest.raises(RuntimeError, match="rate limit exhausted.*GITHUB_TOKEN"):
        public_data.fetch_issue("dbt-labs/dbt", 15914, opener=limited, delay=lambda _: None)


def test_public_evaluation_checks_source_identity_not_just_reference_field(monkeypatch):
    item = public_data.normalize_issue(ISSUE, SOURCE, project_label="timeout")
    monkeypatch.setattr(public_data, "list_public_incidents",
                        lambda **_kwargs: {"incidents": [item], "total": 1})
    assert public_data.evaluate_public_records()["evidence_coverage"] == 1
    item["source_url"] = "https://example.org/unsupported"
    assert public_data.evaluate_public_records()["evidence_coverage"] == 0


def test_issue_title_screens_obvious_credentials():
    item = public_data.normalize_issue({**ISSUE, "title": "Parser fails password=sample-secret",
                                        "body": ""}, SOURCE)
    assert "sample-secret" not in item["title"]
    assert "credential redacted" in item["title"]
