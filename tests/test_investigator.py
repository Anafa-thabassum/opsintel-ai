
import pytest

from app.investigator import (
    _build_run_comparison,
    _classify_evidence_details,
    _completeness,
    assess_root_causes,
)


def test_root_cause_is_not_claimed_as_confirmed():
    incident = {
        "evidence": [
            {"observation": "Source returned only 80 rows"}
        ]
    }

    result = assess_root_causes(incident)

    assert result["confirmed_root_cause"] is None
    assert len(result["candidates"]) > 0


def test_root_cause_candidates_are_supported_observations():
    incident = {
        "evidence": [
            {"observation": "Source returned only 80 rows"},
            {
                "observation": (
                    "Import ended before all expected rows were processed"
                )
            },
        ]
    }

    result = assess_root_causes(incident)

    for candidate in result["candidates"]:
        assert candidate["status"] == "supported_observation"


def test_timeout_evidence_produces_timeout_candidate():
    incident = {
        "evidence": [
            {
                "observation": (
                    "Pipeline timeout: execution exceeded 30 minutes"
                )
            }
        ]
    }

    result = assess_root_causes(incident)

    assert any(
        "time limit" in candidate["cause"].lower()
        for candidate in result["candidates"]
    )


def test_schema_mismatch_evidence_produces_schema_candidate():
    incident = {
        "evidence": [
            {
                "observation": (
                    "Schema mismatch: incoming field price_text "
                    "does not match expected numeric type"
                )
            }
        ]
    }

    result = assess_root_causes(incident)

    assert any(
        "schema" in candidate["cause"].lower()
        for candidate in result["candidates"]
    )


def test_empty_or_benign_evidence_does_not_invent_root_causes():
    evidence_sets = [
        [],
        [{"observation": "Timeout threshold configured at 30 minutes"}],
        [{"observation": "Schema validation passed; schema compatible"}],
        [{"observation": "All dependencies succeeded"}],
    ]

    for evidence in evidence_sets:
        result = assess_root_causes({"evidence": evidence})

        assert result["candidates"] == []
        assert result["confirmed_root_cause"] is None


def test_investigation_deduplicates_pipeline_logs(monkeypatch):
    from app import investigator

    monkeypatch.setattr(
        investigator,
        "get_failed_pipelines",
        lambda: [(1, "daily_sales_import", 100, 80, 20, "FAILED")],
    )

    class FakeResult:
        def __init__(self, rows):
            self.rows = rows

        def fetchall(self):
            return self.rows

        def fetchone(self):
            return self.rows[0] if self.rows else None

    class FakeConnection:
        def execute(self, query, parameters=None):
            if "SELECT DISTINCT" in query:
                if parameters == {"run_id": 101}:
                    return FakeResult([])
                assert parameters == {"run_id": 1}
                return FakeResult([
                    (
                        1,
                        "INFO",
                        "Pipeline started; expected 100 source rows",
                        "2026-10-18 01:00:00",
                    ),
                    (
                        2,
                        "WARN",
                        "Source returned only 80 rows",
                        "2026-10-18 01:01:00",
                    ),
                ])

            if "ROUND(AVG(ACTUAL_ROWS)" in query:
                return FakeResult([(100, 100, 4)])

            if "RUN_STATUS = 'SUCCESS'" in query:
                return FakeResult([
                    (101, 100, 100, "2026-10-17 01:00:00"),
                ])

            assert "PIPELINE_NAME =" in query
            assert parameters == {
                "pipeline_name": "daily_sales_import",
                "run_id": 1,
            }
            return FakeResult([
                (1, "FAILED", 100, 80, "2026-10-18 01:02:00"),
                (101, "SUCCESS", 100, 100, "2026-10-17 01:00:00"),
            ])

        def close(self):
            pass

    monkeypatch.setattr(
        investigator,
        "get_connection",
        lambda: FakeConnection(),
    )

    result = investigator.investigate_pipeline(1)

    log_evidence = [
        item
        for item in result["evidence"]
        if item["type"] == "pipeline_log"
    ]

    assert [item["log_id"] for item in log_evidence] == [1, 2]
    assert log_evidence[0]["timestamp"] == "2026-10-18 01:00:00"
    assert result["history"][1]["status"] == "SUCCESS"
    assert result["comparison"]["last_successful_run"]["run_id"] == 101
    assert result["comparison"]["current_run"]["completeness_pct"] == 80
    assert result["comparison"]["historical_baseline"] == {
        "average_actual_rows": 100.0,
        "average_completeness_pct": 100.0,
        "successful_runs": 4,
    }
    assert len(result["comparison"]["new_or_changed_logs"]) == 2


@pytest.mark.parametrize(("expected", "actual", "result"), [
    (100, 80, 80.0),
    (0, 0, 100.0),
    (None, 10, None),
    (10, None, None),
    (None, None, None),
    (0, 5, None),
])
def test_completeness_handles_nullable_counts(expected, actual, result):
    assert _completeness(expected, actual) == result


def test_comparison_preserves_unknown_counts():
    comparison = _build_run_comparison(
        10,
        None,
        80,
        [],
        (9, 100, None, "2026-10-19 01:00:00"),
        (100, None, 1),
        [],
    )

    assert comparison["status"] == "available"
    assert comparison["current_run"]["expected_rows"] is None
    assert comparison["last_successful_run"]["actual_rows"] is None
    assert all(item["delta"] is None for item in comparison["differences"])


def test_investigation_history_stops_at_selected_run(monkeypatch):
    from app import investigator

    monkeypatch.setattr(
        investigator,
        "get_failed_pipelines",
        lambda: [(10, "orders", 100, 80, 20, "FAILED", 0)],
    )

    class Result:
        def __init__(self, rows):
            self.rows = rows

        def fetchall(self):
            return self.rows

        def fetchone(self):
            return self.rows[0] if self.rows else None

    class Connection:
        def __init__(self):
            self.queries = []

        def execute(self, query, parameters=None):
            self.queries.append((query, parameters))
            if "SELECT DISTINCT" in query:
                return Result([])
            if "ROUND(AVG(ACTUAL_ROWS)" in query:
                return Result([(100, 100, 1)])
            if "RUN_STATUS = 'SUCCESS'" in query:
                return Result([
                    (9, 100, 100, "2026-10-19 01:00:00")
                    if "AND RUN_ID < {run_id!d}" in query
                    else (11, 100, 100, "2026-10-19 03:00:00")
                ])
            history = [
                (11, "SUCCESS", 100, 100, "2026-10-19 03:00:00"),
                (10, "FAILED", 100, 80, "2026-10-19 02:00:00"),
                (9, "SUCCESS", 100, 100, "2026-10-19 01:00:00"),
            ]
            return Result(
                history[1:] if "AND RUN_ID <= {run_id!d}" in query else history
            )

        def close(self):
            pass

    connection = Connection()
    monkeypatch.setattr(investigator, "get_connection", lambda: connection)

    result = investigator.investigate_pipeline(10)

    assert [row["run_id"] for row in result["history"]] == [10, 9]
    assert result["comparison"]["last_successful_run"]["run_id"] == 9
    history_query = next(
        query for query, _ in connection.queries
        if "LIMIT 5" in query and "RUN_STATUS = 'SUCCESS'" not in query
    )
    success_queries = [
        query for query, _ in connection.queries
        if "RUN_STATUS = 'SUCCESS'" in query
    ]
    assert "AND RUN_ID <= {run_id!d}" in history_query
    assert all("AND RUN_ID < {run_id!d}" in query for query in success_queries)


def test_investigation_with_missing_counts_keeps_log_evidence(monkeypatch):
    from app import investigator

    monkeypatch.setattr(
        investigator,
        "get_failed_pipelines",
        lambda: [(1, "unknown_counts", None, None, None, "FAILED", None)],
    )

    class Result:
        def __init__(self, rows):
            self.rows = rows

        def fetchall(self):
            return self.rows

        def fetchone(self):
            return self.rows[0] if self.rows else None

    class Connection:
        def execute(self, query, parameters=None):
            if "SELECT DISTINCT" in query:
                return Result([(
                    8,
                    "ERROR",
                    "Pipeline execution exceeded the 30 minute time limit",
                    "2026-10-19 01:00:00",
                )])
            if "ROUND(AVG(ACTUAL_ROWS)" in query:
                return Result([(None, None, 0)])
            return Result([])

        def close(self):
            pass

    monkeypatch.setattr(investigator, "get_connection", Connection)

    result = investigator.investigate_pipeline(1)

    assert result["expected_rows"] is None
    assert result["actual_rows"] is None
    assert result["missing_rows"] is None
    assert result["excess_rows"] is None
    assert result["category"] == "timeout"
    assert result["history"] == []
    assert result["comparison"]["status"] == "unavailable"
    assert any(item["type"] == "pipeline_log" for item in result["evidence"])

def test_early_termination_takes_priority_over_missing_rows():
    from app.investigator import classify_evidence

    category, hypothesis, recommended_action = classify_evidence(
        ["Import ended before all expected rows were processed"],
        20,
    )

    assert category == "early_termination"
    assert "not confirmed" in hypothesis
    assert recommended_action


def test_missing_rows_without_early_termination_are_incomplete_data():
    from app.investigator import classify_evidence

    category, hypothesis, recommended_action = classify_evidence(
        ["Source returned only 80 rows"],
        20,
    )

    assert category == "incomplete_data"
    assert "not confirmed" in hypothesis
    assert recommended_action

def test_equal_row_counts_do_not_add_row_count_candidate():
    from app.investigator import assess_root_causes

    incident = {
        "expected_rows": 500,
        "actual_rows": 500,
        "evidence": [
            {"observation": "Pipeline status is FAILED"},
            {
                "observation": "Expected 500 rows, but received 500"
            },
            {
                "observation": (
                    "[ERROR] Pipeline execution exceeded "
                    "the 30 minute time limit"
                )
            },
        ],
    }

    result = assess_root_causes(incident)

    causes = [item["cause"] for item in result["candidates"]]

    assert "Pipeline execution exceeded a time limit" in causes
    assert "Expected and actual row counts differ" not in causes
    assert result["confirmed_root_cause"] is None


def test_delayed_run_evidence_remains_unconfirmed():
    from app.investigator import classify_evidence

    category, hypothesis, next_action = classify_evidence(
        ["Pipeline started late and missed its SLA"],
        0,
    )

    assert category == "delayed_run"
    assert "not confirmed" in hypothesis
    assert "scheduled" in next_action


def test_excess_rows_are_classified_as_possible_duplicates():
    from app.investigator import classify_evidence

    category, hypothesis, _ = classify_evidence(
        [],
        -20,
        expected_rows=100,
        actual_rows=120,
    )

    assert category == "duplicate_data"
    assert "duplication point is unknown" in hypothesis


def test_conflicting_completion_logs_are_not_forced_to_a_cause():
    from app.investigator import classify_evidence

    category, hypothesis, _ = classify_evidence(
        [
            "Pipeline completed successfully",
            "ERROR: worker failed after final write",
        ],
        0,
    )

    assert category == "conflicting_evidence"
    assert "cannot be resolved" in hypothesis


def test_classification_reports_confidence_and_deterministic_tie_break():
    result = _classify_evidence_details(
        ["Execution timed out after invalid cast in the final batch"],
        0,
    )

    assert result["result"][0] == "timeout"
    assert result["confidence"] == "low"
    assert result["matched_categories"] == ["timeout", "schema_mismatch"]
    assert "documented precedence" in result["tie_break_reason"]


def test_single_explicit_signal_has_medium_qualitative_confidence():
    result = _classify_evidence_details(
        ["Execution exceeded the configured time limit"],
        0,
    )

    assert result["result"][0] == "timeout"
    assert result["confidence"] == "medium"
    assert result["matched_categories"] == ["timeout"]


def test_unknown_signal_explains_why_confidence_is_low():
    result = _classify_evidence_details(
        ["Worker exited with opaque code ZX-41"],
        0,
    )

    assert result["result"][0] == "unclassified"
    assert result["confidence"] == "low"
    assert result["matched_categories"] == []
    assert result["tie_break_reason"] == "No supported classifier signal matched."


def test_candidates_include_traceable_supporting_evidence():
    incident = {
        "expected_rows": 100,
        "actual_rows": 80,
        "category": "early_termination",
        "evidence": [
            {
                "type": "row_count",
                "observation": "Expected 100 rows, but received 80",
                "source": "OPSINTEL.PIPELINE_RUNS",
                "run_id": 1,
            },
            {
                "observation": (
                    "Import ended before all expected rows were processed"
                ),
                "source": "OPSINTEL.PIPELINE_LOGS",
                "log_id": 3,
            },
        ],
    }

    result = assess_root_causes(incident)

    assert result["resolution_status"] == "candidates_only"
    assert result["candidates"]
    assert all(item["supporting_evidence"] for item in result["candidates"])
    references = {
        support["reference"]
        for candidate in result["candidates"]
        for support in candidate["supporting_evidence"]
    }
    assert "OPSINTEL.PIPELINE_RUNS · RUN-1" in references
    assert "OPSINTEL.PIPELINE_LOGS · LOG-3" in references


def test_insufficient_evidence_is_explicitly_unresolved():
    result = assess_root_causes({
        "category": "unclassified",
        "expected_rows": 300,
        "actual_rows": 300,
        "evidence": [
            {
                "observation": "Remote endpoint emitted opaque code ZX-41",
                "source": "OPSINTEL.PIPELINE_LOGS",
                "log_id": 13,
            }
        ],
    })

    assert result["candidates"] == []
    assert result["resolution_status"] == "unresolved"
    assert "does not support" in result["unresolved_reason"]


def test_run_differences_link_to_supported_candidates():
    from app.investigator import attach_comparison_support

    incident = {
        "comparison": {
            "status": "available",
            "differences": [{
                "metric": "New or changed log messages",
                "delta": 1,
                "evidence_refs": ["OPSINTEL.PIPELINE_LOGS · LOG-3"],
            }],
        }
    }
    assessment = {
        "candidates": [{
            "cause": "Processing ended early",
            "supporting_evidence": [{
                "reference": "OPSINTEL.PIPELINE_LOGS · LOG-3",
                "observation": "Import ended before completion",
            }],
        }]
    }

    attach_comparison_support(incident, assessment)

    assert incident["comparison"]["differences"][0]["supports"] == [
        "Processing ended early"
    ]

