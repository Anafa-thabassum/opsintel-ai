import json
from pathlib import Path

import pytest

from app.classification import classify_incident, normalize_evidence


@pytest.mark.parametrize(("evidence", "context", "expected"), [
    (["Scheduler marked the run started late after its start window."], {}, "delayed_run"),
    ([{"reference": "RUN-2", "fields": {
        "scheduled_at": "2026-02-03T08:00:00Z",
        "started_at": "2026-02-03T08:35:00Z",
        "sla_seconds": 600,
    }}], {}, "delayed_run"),
    (["Duplicate business keys were found in the target partition."], {}, "duplicate_data"),
    ([{"reference": "CHECK-4", "fields": {"duplicate_count": 3}}], {}, "duplicate_data"),
    (["Statement timeout event reached during query execution."], {}, "timeout"),
    (["TaskImportTimeout raised while parsing a workflow definition."], {}, "timeout"),
    (["Workflow import timeout after a configured execution limit."], {}, "timeout"),
    (["Query was canceled after its configured statement timeout."], {}, "timeout"),
    (["Invalid cast prevented writing the requested value."], {}, "schema_mismatch"),
    ([{"reference": "SCHEMA-1", "fields": {
        "expected_type": "DECIMAL", "actual_type": "VARCHAR",
    }}], {}, "schema_mismatch"),
    (["Required upstream artifact was unavailable to the scheduled transform."], {}, "dependency_failure"),
    ([{"reference": "DEP-1", "fields": {
        "required": True, "dependency_name": "extract_orders",
        "dependency_status": "failed",
    }}], {}, "dependency_failure"),
    (["Worker terminated before the final checkpoint was committed."], {}, "early_termination"),
    ([{"reference": "RUN-9", "fields": {
        "exit_code": 137, "completed": False,
    }}], {}, "early_termination"),
    ([{"reference": "COUNTS-1", "fields": {
        "expected_rows": 250, "actual_rows": 214,
    }}], {}, "incomplete_data"),
    (["The reconciliation expected 250 records and processed 214."], {}, "incomplete_data"),
    (["Validation reports 214 rows written."], {}, "unclassified"),
])
def test_general_signal_regressions(evidence, context, expected):
    """General taxonomy contracts; not copied from reviewer holdout cases."""
    result = classify_incident(evidence, context)
    assert result["result"][0] == expected
    if expected != "unclassified":
        assert result["classification"]["status"] == "supported"
        assert result["classification"]["resolution_status"] == "candidate_only"
        assert result["classification"]["confirmed_root_cause"] is None


def test_normalization_preserves_raw_values_and_marks_malformed_metadata():
    evidence, errors = normalize_evidence([{
        "reference": "LOG-77",
        "observation": "Raw message  Expected rows: ?",
        "timestamp": "not-a-timestamp",
        "fields": {"actual_rows": "many"},
    }])

    assert evidence[0]["reference"] == "LOG-77"
    assert evidence[0]["raw_observation"] == "Raw message  Expected rows: ?"
    assert evidence[0]["fields"]["actual_rows"] is None
    assert evidence[0]["malformed_fields"] == ["actual_rows"]
    assert evidence[0]["timestamp"] == "not-a-timestamp"
    assert errors


def test_negated_signal_does_not_hide_a_different_positive_clause():
    result = classify_incident([
        {"reference": "LOG-1", "observation": (
            "No timeout occurred, but the schema validator rejected the field format."
        )}
    ])

    assert result["result"][0] == "schema_mismatch"
    assert {signal["category"]: signal["polarity"] for signal in result["signals"]} == {
        "timeout": "negates",
        "schema_mismatch": "supports",
    }


def test_multiple_supported_symptoms_are_retained_with_stable_primary():
    result = classify_incident([
        {"reference": "LOG-1", "observation": (
            "The statement timed out after a validator rejected a numeric field format."
        )}
    ])

    assert result["result"][0] == "timeout"
    assert result["classification"]["symptom_category"] == "timeout"
    assert result["classification"]["secondary_categories"] == ["schema_mismatch"]
    assert result["classification"]["status"] == "supported"


def test_conflicting_row_counts_keep_both_source_references_and_abstain():
    result = classify_incident([
        {"reference": "SUMMARY-1", "run_id": 4, "observation": "The run reports 1200 rows written."},
        {"reference": "VALIDATION-1", "run_id": 4, "observation": "The validator reports 1150 rows written."},
    ])

    assert result["result"][0] == "conflicting_evidence"
    assert result["classification"]["status"] == "unresolved"
    conflict = result["conflicts"][0]
    assert set(conflict["evidence_refs"]) == {"SUMMARY-1", "VALIDATION-1"}


def test_opposite_terminal_states_are_a_conflict_only_within_same_run():
    result = classify_incident([
        {"reference": "RUN-1-OK", "run_id": 1, "observation": "Pipeline completed successfully."},
        {"reference": "RUN-1-ERR", "run_id": 1, "observation": "Pipeline status is FAILED."},
        {"reference": "RUN-2-OK", "run_id": 2, "observation": "Pipeline completed successfully."},
    ])

    assert result["result"][0] == "conflicting_evidence"
    conflict = result["conflicts"][0]
    assert set(conflict["evidence_refs"]) == {"RUN-1-OK", "RUN-1-ERR"}


def test_excess_counts_are_not_duplicate_data_without_duplicate_evidence():
    result = classify_incident([], {
        "run_id": 12,
        "expected_rows": 100,
        "actual_rows": 110,
    })

    assert result["result"][0] == "unclassified"
    assert any(signal["category"] == "excess_rows" for signal in result["signals"])


def test_repeated_and_irrelevant_evidence_does_not_override_independent_symptom():
    evidence = [
        {"reference": "LOG-T", "observation": "Statement timed out after its configured limit."},
        {"reference": "LOG-S", "observation": "Schema validator rejected incompatible field type."},
        {"reference": "LOG-T", "observation": "Statement timed out after its configured limit."},
        {"reference": "LOG-N", "observation": "Operator opened the dashboard."},
    ]
    result = classify_incident(evidence)
    assert result["result"][0] == "timeout"
    assert result["classification"]["secondary_categories"] == ["schema_mismatch"]
    assert result["classification"]["confirmed_root_cause"] is None


def test_empty_and_unseen_message_abstain_without_invented_cause():
    for evidence in ([], [{"reference": "LOG-X", "observation": "Remote ZX-41 payload fragment was emitted."}]):
        result = classify_incident(evidence)
        assert result["result"][0] == "unclassified"
        assert result["classification"]["resolution_status"] == "unresolved"
        assert result["classification"]["confirmed_root_cause"] is None


def test_public_development_corpus_v2_labels_and_provenance():
    root = Path(__file__).resolve().parents[1]
    corpus = root / "evaluation" / "public_development_corpus_v2.jsonl"
    cases = [json.loads(line) for line in corpus.read_text().splitlines()]

    assert cases
    assert {case["dataset_role"] for case in cases} <= {
        "development_positive_provisional",
        "development_abstention_taxonomy_boundary",
    }
    assert all(case["provenance"]["original_primary_source_url"] for case in cases)
    assert all(case["provenance"]["primary_source_retrieved_on"] == "2026-10-30" for case in cases)

    for case in cases:
        result = classify_incident(case["evidence_items"])
        assert result["result"][0] == case["classification"]["legacy_category"]
        assert result["classification"]["resolution_status"] == case["resolution_status"]
        assert result["classification"]["confirmed_root_cause"] is None
        for signal in result["classification"]["signals"]:
            assert signal["evidence_refs"]
            assert set(signal["evidence_refs"]) <= {
                item["reference"] for item in case["evidence_items"]
            }
