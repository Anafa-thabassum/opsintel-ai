"""Contract tests for the Exasol memory boundary; no fake accuracy claims."""

import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app import memory
from app.fingerprint import FINGERPRINT_VERSION, compare_fingerprints, fingerprint_incident, normalize_log
from app.main import app
from scripts.migrate_database import MIGRATIONS, migrate
from scripts.setup_database import load_statements


client = TestClient(app)
INCIDENT = {
    "run_id": 1, "pipeline_name": "orders", "category": "timeout",
    "classification": {"symptom_category": "timeout"},
    "expected_rows": 100, "actual_rows": 80,
    "evidence": [{"type": "pipeline_log", "reference": "OPSINTEL.PIPELINE_LOGS · LOG-7",
                  "observation": "SQLSTATE 57014 query timed out on column order_id for run 123 at 2026-10-30 12:30:00"}],
}
PACKET = [{"reference": "OPSINTEL.PIPELINE_LOGS · LOG-7",
           "excerpt": "SQLSTATE 57014 query timed out on column order_id for run 123 at 2026-10-30 12:30:00",
           "source_uri": None, "kind": "symptom"},
          {"reference": "https://example.org/lock-trace/7", "source_uri": "https://example.org/lock-trace/7",
           "excerpt": "The lock trace ties the wait to this query run.", "kind": "causal"}]


def test_fingerprint_removes_volatile_values_but_keeps_diagnostic_tokens():
    first = normalize_log("SQLSTATE 57014 timeout order_id at 2026-10-30 12:30:00 run 123 /tmp/a.csv")
    second = normalize_log("SQLSTATE 57014 timeout order_id at 2026-10-31 14:00:00 run 987 /tmp/b.csv")
    assert first == second
    assert "sqlstate57014" in first and "order_id" in first
    assert "123" not in first and "/tmp" not in first
    assert fingerprint_incident(INCIDENT)["version"] == FINGERPRINT_VERSION


def test_similarity_threshold_is_configurable_and_bounded(monkeypatch):
    monkeypatch.delenv("OPSINTEL_MEMORY_MIN_SIMILARITY", raising=False)
    assert memory.min_similarity_threshold() == 0.42
    monkeypatch.setenv("OPSINTEL_MEMORY_MIN_SIMILARITY", "0.73")
    assert memory.min_similarity_threshold() == 0.73
    for invalid in ("1.1", "abc"):
        monkeypatch.setenv("OPSINTEL_MEMORY_MIN_SIMILARITY", invalid)
        with pytest.raises(ValueError, match="from 0 to 1"):
            memory.min_similarity_threshold()


def test_similarity_explains_matches_and_rejects_contradictions():
    first = fingerprint_incident(INCIDENT)
    equivalent = fingerprint_incident({**INCIDENT, "run_id": 2})
    same = compare_fingerprints(first, equivalent)
    assert same["score"] == 1 and same["eligible"]
    different = compare_fingerprints(first, {**equivalent, "features": {"symptom_category": "schema_mismatch"}})
    assert not different["eligible"]
    assert "symptom_category" in different["differing_features"]
    version = compare_fingerprints(first, {**equivalent, "version": "future-v2"})
    assert not version["eligible"]


def test_submission_requires_traceable_evidence_and_existing_confirmation_blocks_duplicate(monkeypatch):
    monkeypatch.setattr(memory, "get_confirmed", lambda run_id: None)
    monkeypatch.setattr(memory, "_transaction", lambda operation: None)
    result = memory.submit_hypothesis(INCIDENT, category="timeout", description="A lock wait caused the configured timeout",
                                      evidence=PACKET, actor_id="alice")
    assert result["status"] == "pending"
    with pytest.raises(ValueError, match="resolve"):
        memory.submit_hypothesis(INCIDENT, category="timeout", description="A lock wait caused the configured timeout",
                                 evidence=[{"reference": "EVIDENCE-1", "excerpt": "unverified", "kind": "symptom"}], actor_id="alice")
    with pytest.raises(ValueError, match="match"):
        memory.submit_hypothesis(INCIDENT, category="timeout", description="A lock wait caused the configured timeout",
                                 evidence=[{**PACKET[0], "excerpt": "invented evidence"}], actor_id="alice")
    with pytest.raises(ValueError, match="distinct symptom and causal"):
        memory.submit_hypothesis(INCIDENT, category="timeout", description="A lock wait caused the configured timeout",
                                 evidence=[PACKET[0]], actor_id="alice")
    monkeypatch.setattr(memory, "get_confirmed", lambda run_id: {"incident_id": "old", "status": "active"})
    with pytest.raises(memory.MemoryConflict, match="already"):
        memory.submit_hypothesis(INCIDENT, category="timeout", description="A lock wait caused the configured timeout",
                                 evidence=PACKET, actor_id="alice")


def _submission():
    return {"submission_id": "s1", "run_id": 1, "pipeline_name": "orders", "kind": "new",
            "source_incident_id": None, "category": "timeout",
            "cause_description": "A lock wait caused the configured timeout",
            "evidence": PACKET, "submitted_classification": {"status": "supported", "symptom_category": "timeout", "conflicts": []},
            "fingerprint": fingerprint_incident(INCIDENT),
            "submitted_by": "alice", "status": "pending"}


def _checklist():
    return {"version": memory.CHECKLIST_VERSION, "unresolved_conflicts": [],
            "criteria": [{"id": criterion, "passed": True, "method": "Compared source records",
                          "result": "Evidence supports the asserted mechanism",
                          "evidence_refs": [PACKET[0]["reference"] if criterion == memory.CLASS_CRITERIA["timeout"][0] else PACKET[1]["reference"]]}
                         for criterion in (*memory.CLASS_CRITERIA["timeout"], *memory.COMMON_CRITERIA)]}


def test_review_rejects_self_approval_missing_checks_and_conflicts(monkeypatch):
    monkeypatch.setattr(memory, "get_submission", lambda submission_id: _submission())
    with pytest.raises(memory.MemoryConflict, match="differ"):
        memory.review_hypothesis("s1", decision="approve", rationale="Verified source and limit", checklist=_checklist(), reviewer_id="alice")
    missing = _checklist()
    missing["criteria"].pop()
    with pytest.raises(ValueError, match="Every required"):
        memory.review_hypothesis("s1", decision="approve", rationale="Verified source and limit", checklist=missing, reviewer_id="bob")
    conflict = _checklist()
    conflict["unresolved_conflicts"] = ["Cancellation preceded timeout"]
    with pytest.raises(ValueError, match="contradictions"):
        memory.review_hypothesis("s1", decision="approve", rationale="Verified source and limit", checklist=conflict, reviewer_id="bob")
    submission = _submission()
    submission["submitted_classification"]["conflicts"] = [{"type": "terminal_state"}]
    monkeypatch.setattr(memory, "get_submission", lambda submission_id: submission)
    with pytest.raises(ValueError, match="classifier conflicts"):
        memory.review_hypothesis("s1", decision="approve", rationale="Verified source and limit", checklist=_checklist(), reviewer_id="bob")


class _Result:
    def __init__(self, row=None):
        self.row = row

    def fetchone(self):
        return self.row


class _Connection:
    def __init__(self, row=None):
        self.row = row
        self.statements = []
        self.committed = False
        self.rolled_back = False

    def set_autocommit(self, value):
        assert value is False

    def execute(self, query, values=None):
        self.statements.append((query, values))
        return _Result(self.row if "SELECT" in query else None)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        pass


def test_approval_writes_confirmation_features_audit_and_review_atomically(monkeypatch):
    connection = _Connection()
    monkeypatch.setattr(memory, "get_submission", lambda submission_id: _submission())
    monkeypatch.setattr(memory, "get_connection", lambda: connection)
    result = memory.review_hypothesis("s1", decision="approve", rationale="Verified lock wait and timeout", checklist=_checklist(), reviewer_id="bob")
    sql = "\n".join(query for query, _ in connection.statements)
    assert result["confirmed_root_cause"] == _submission()["cause_description"]
    assert all(name in sql for name in ("CONFIRMED_INCIDENTS", "INCIDENT_FEATURES", "INCIDENT_AUDIT", "INCIDENT_SUBMISSIONS"))
    assert connection.committed and not connection.rolled_back


def _confirmed_row():
    return ("confirmed-1", 1, "orders", "timeout", "An earlier explanation",
            FINGERPRINT_VERSION, json.dumps(fingerprint_incident(INCIDENT)), json.dumps(PACKET),
            "bob", "2026-10-30", "active", None, 1)


def test_correction_retains_audit_and_stales_old_matches(monkeypatch):
    submission = {**_submission(), "kind": "correction", "source_incident_id": "confirmed-1"}
    connection = _Connection(_confirmed_row())
    monkeypatch.setattr(memory, "get_submission", lambda submission_id: submission)
    monkeypatch.setattr(memory, "get_connection", lambda: connection)
    result = memory.review_hypothesis("s1", decision="approve", rationale="New causal record supersedes old", checklist=_checklist(), reviewer_id="bob")
    sql = "\n".join(query for query, _ in connection.statements)
    assert result["incident_id"] == "confirmed-1"
    assert "SET MATCH_STATUS = 'stale'" in sql
    assert "REVISION =" in sql
    assert "INCIDENT_AUDIT" in sql and connection.committed


def test_revoked_record_can_be_replaced_only_through_review(monkeypatch):
    revoked = {"incident_id": "confirmed-1", "status": "revoked"}
    monkeypatch.setattr(memory, "get_confirmed", lambda run_id: revoked)
    transaction = memory._transaction
    monkeypatch.setattr(memory, "_transaction", lambda operation: None)
    result = memory.submit_hypothesis(
        INCIDENT, category="timeout", description="A verified replacement for the revoked cause",
        evidence=PACKET, actor_id="alice", kind="correction", source_incident_id="confirmed-1",
    )
    assert result["status"] == "pending"
    monkeypatch.setattr(memory, "_transaction", transaction)
    submission = {**_submission(), "kind": "correction", "source_incident_id": "confirmed-1"}
    row = list(_confirmed_row())
    row[10] = "revoked"
    connection = _Connection(tuple(row))
    monkeypatch.setattr(memory, "get_submission", lambda submission_id: submission)
    monkeypatch.setattr(memory, "get_connection", lambda: connection)
    approved = memory.review_hypothesis(
        "s1", decision="approve", rationale="New source audit supports this cause",
        checklist=_checklist(), reviewer_id="bob",
    )
    assert approved["incident_id"] == "confirmed-1"
    assert any("STATUS = 'active'" in query for query, _ in connection.statements)
    assert connection.committed


def test_revocation_excludes_old_matches_and_keeps_history(monkeypatch):
    connection = _Connection(_confirmed_row())
    monkeypatch.setattr(memory, "get_connection", lambda: connection)
    result = memory.revoke_confirmation("confirmed-1", rationale="Source audit disproved the diagnosis", reviewer_id="bob")
    sql = "\n".join(query for query, _ in connection.statements)
    assert result["status"] == "revoked"
    assert "SET MATCH_STATUS = 'stale'" in sql
    assert "INCIDENT_AUDIT" in sql and connection.committed


def test_failed_transaction_rolls_back(monkeypatch):
    connection = _Connection()
    monkeypatch.setattr(memory, "get_connection", lambda: connection)
    with pytest.raises(RuntimeError):
        memory._transaction(lambda _: (_ for _ in ()).throw(RuntimeError("database failure")))
    assert connection.rolled_back and not connection.committed


def test_similar_retrieval_skips_revoked_and_self_and_returns_candidate(monkeypatch):
    historical = {"incident_id": "confirmed-2", "run_id": 2, "confirmed_description": "Verified lock wait",
                  "confirmed_category": "timeout", "fingerprint": fingerprint_incident(INCIDENT),
                  "evidence": [], "confirmed_by": "reviewer-b",
                  "confirmed_at": "2026-10-30", "status": "active"}
    monkeypatch.setattr(memory, "_read", lambda operation: ([historical], {}))
    result = memory.similar_incidents(INCIDENT, record=False)
    assert result["status"] == "candidates_available"
    assert result["matches"][0]["status"] == "candidate"
    assert "engineer verification required" in result["matches"][0]["label"]
    assert result["matches"][0]["historical_evidence"] == []
    assert "probability" in result["score_notice"]
    monkeypatch.setattr(memory, "_read", lambda operation: ([], {}))
    assert memory.similar_incidents(INCIDENT, record=False)["status"] == "unresolved"
    monkeypatch.setattr(memory, "_read", lambda operation: ([historical], {"confirmed-2": ("match-1", "rejected")}))
    assert memory.similar_incidents(INCIDENT, record=False)["matches"] == []


def test_memory_api_requires_explicit_role_grants(monkeypatch):
    monkeypatch.delenv("OPSINTEL_AUTH_TOKENS_JSON", raising=False)
    assert client.get("/memory/incidents").status_code == 503
    monkeypatch.setenv("OPSINTEL_AUTH_TOKENS_JSON", json.dumps({"investigator-secret": {"actor_id": "alice", "role": "investigator"},
                                                              "reviewer-secret": {"actor_id": "bob", "role": "reviewer"}}))
    assert client.get("/memory/incidents").status_code == 401
    with patch("app.main.memory.list_confirmed", return_value=[]):
        assert client.get("/memory/incidents", headers={"Authorization": "Bearer investigator-secret"}).status_code == 200
    payload = {"decision": "reject", "rationale": "Causal evidence does not support it",
               "checklist": {"version": memory.CHECKLIST_VERSION, "criteria": [], "unresolved_conflicts": []}}
    assert client.post("/memory/submissions/s1/review", json=payload,
                       headers={"Authorization": "Bearer investigator-secret"}).status_code == 403


def test_submissions_endpoint_scopes_investigator_and_exposes_reviewer_role(monkeypatch):
    monkeypatch.setenv("OPSINTEL_AUTH_TOKENS_JSON", json.dumps({
        "investigator-secret": {"actor_id": "alice", "role": "investigator"},
        "reviewer-secret": {"actor_id": "bob", "role": "reviewer"},
    }))
    with patch("app.main.memory.list_submissions", return_value=[]) as list_items:
        investigator = client.get("/memory/submissions", headers={"Authorization": "Bearer investigator-secret"})
        assert investigator.json()["role"] == "investigator"
        list_items.assert_called_with(actor_id="alice", reviewer=False)
        reviewer = client.get("/memory/submissions", headers={"Authorization": "Bearer reviewer-secret"})
        assert reviewer.json()["role"] == "reviewer"
        list_items.assert_called_with(actor_id="bob", reviewer=True)


def test_migration_is_additive_and_has_no_drop():
    statements = load_statements(MIGRATIONS / "001_verified_incident_memory.sql")
    assert len(statements) == 5
    assert all(statement.startswith("CREATE TABLE IF NOT EXISTS") for statement in statements)


def test_migration_check_reports_pending_without_writes():
    class Connection:
        def execute(self, query):
            assert "EXA_ALL_TABLES" in query
            return _Result((0,))
    result = migrate(Connection(), apply=False)
    assert "001_verified_incident_memory.sql" in result["pending"]
