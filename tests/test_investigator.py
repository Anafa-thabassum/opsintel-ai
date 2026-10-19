
from app.investigator import assess_root_causes


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


def test_empty_evidence_does_not_invent_root_causes():
    incident = {"evidence": []}

    result = assess_root_causes(incident)

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

    class FakeConnection:
        def execute(self, query, parameters=None):
            if "SELECT DISTINCT" in query:
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

            assert "PIPELINE_NAME =" in query
            assert parameters == {"pipeline_name": "daily_sales_import"}
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

