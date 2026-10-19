import csv
from collections import Counter
from pathlib import Path

import pytest

from app.investigator import classify_evidence
from scripts.summarize_impact_study import render_markdown, summarize


FIELDS = [
    "trial_id",
    "participant_id",
    "trial_order",
    "case_id",
    "condition",
    "seconds",
    "diagnosis",
    "evidence_references",
    "confidence",
    "unsafe_confirmation",
    "llm_enabled",
    "protocol_deviation",
]
ASSIGNMENT_FIELDS = [
    "trial_id",
    "participant_id",
    "trial_order",
    "case_id",
    "condition",
]


def write_csv(path, fields, rows):
    with path.open("w", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def study_files(tmp_path):
    key = tmp_path / "key.csv"
    assignment = tmp_path / "assignment.csv"
    results = tmp_path / "results.csv"
    write_csv(key, ["case_id", "expected_category"], [
        {"case_id": "c1", "expected_category": "timeout"},
        {"case_id": "c2", "expected_category": "schema_mismatch"},
    ])
    assignments = [
        {"trial_id": "p1-t1", "participant_id": "p1", "trial_order": 1, "case_id": "c1", "condition": "manual"},
        {"trial_id": "p1-t2", "participant_id": "p1", "trial_order": 2, "case_id": "c2", "condition": "opsintel"},
        {"trial_id": "p2-t1", "participant_id": "p2", "trial_order": 1, "case_id": "c1", "condition": "opsintel"},
        {"trial_id": "p2-t2", "participant_id": "p2", "trial_order": 2, "case_id": "c2", "condition": "manual"},
    ]
    write_csv(assignment, ASSIGNMENT_FIELDS, assignments)
    return key, assignment, results, assignments


def completed_rows(assignments):
    seconds = {"p1-t1": 120, "p1-t2": 60, "p2-t1": 50, "p2-t2": 100}
    diagnoses = {
        "p1-t1": "timeout",
        "p1-t2": "schema_mismatch",
        "p2-t1": "timeout",
        "p2-t2": "schema_mismatch",
    }
    return [
        {
            **assignment,
            "seconds": seconds[assignment["trial_id"]],
            "diagnosis": diagnoses[assignment["trial_id"]],
            "evidence_references": "LOG-1",
            "confidence": 4,
            "unsafe_confirmation": "false",
            "llm_enabled": "false",
            "protocol_deviation": "",
        }
        for assignment in assignments
    ]


def test_complete_calculations_are_reproducible_and_noncausal(tmp_path):
    key, assignment, results, assignments = study_files(tmp_path)
    write_csv(results, FIELDS, completed_rows(assignments))

    first = summarize(results, key, assignment)
    second = summarize(results, key, assignment)

    assert first == second
    assert first["study_status"] == "complete"
    assert first["comparison_ready"] is True
    assert first["median_time_difference_pct"] == 50.0
    assert first["conditions"]["opsintel"]["correct_pct"] == 100.0
    assert first["conditions"]["opsintel"]["evidence_traceability_pct"] == 100.0
    assert first["study_target_met"] is False
    assert first["time_saving_claim_supported"] is False
    assert first["causal_impact_claim_supported"] is False
    assert "not met" in render_markdown(first)


def test_blank_frozen_template_reports_pending_without_improvement_claim():
    root = Path(__file__).resolve().parents[1]

    report = summarize(root / "evaluation/impact_template.csv")

    assert report["study_status"] == "pending"
    assert report["assigned_trials"] == 40
    assert report["completed_trials"] == 0
    assert report["pending_trials"] == 40
    assert report["comparison_ready"] is False
    assert report["median_time_difference_pct"] is None
    assert report["time_saving_claim_supported"] is False
    rendered = render_markdown(report)
    assert "No measured improvement" in rendered
    assert "No condition comparison was generated" in rendered


def test_malformed_record_schema_is_rejected(tmp_path):
    key, assignment, results, assignments = study_files(tmp_path)
    fields = [field for field in FIELDS if field != "protocol_deviation"]
    write_csv(results, fields, completed_rows(assignments))

    with pytest.raises(ValueError, match="protocol_deviation"):
        summarize(results, key, assignment)


def test_partial_measurement_is_reported_and_not_compared(tmp_path):
    key, assignment, results, assignments = study_files(tmp_path)
    rows = completed_rows(assignments)
    rows[0]["diagnosis"] = ""
    write_csv(results, FIELDS, rows)

    report = summarize(results, key, assignment)

    assert report["study_status"] == "pending"
    assert report["completed_trials"] == 3
    assert report["incomplete_trials"] == 1
    assert report["incomplete_trial_ids"] == ["p1-t1"]
    assert report["comparison_ready"] is False
    assert report["median_time_difference_pct"] is None
    assert report["time_saving_claim_supported"] is False


def test_duplicate_trial_id_is_rejected(tmp_path):
    key, assignment, results, assignments = study_files(tmp_path)
    rows = completed_rows(assignments)
    rows[1]["trial_id"] = rows[0]["trial_id"]
    write_csv(results, FIELDS, rows)

    with pytest.raises(ValueError, match="duplicate trial_id"):
        summarize(results, key, assignment)


@pytest.mark.parametrize("duration", ["0", "-1", "nan", "inf", "not-a-number"])
def test_invalid_duration_is_rejected(tmp_path, duration):
    key, assignment, results, assignments = study_files(tmp_path)
    rows = completed_rows(assignments)
    rows[0]["seconds"] = duration
    write_csv(results, FIELDS, rows)

    with pytest.raises(ValueError, match="seconds must be a positive number"):
        summarize(results, key, assignment)


def test_llm_enabled_trial_is_rejected(tmp_path):
    key, assignment, results, assignments = study_files(tmp_path)
    rows = completed_rows(assignments)
    rows[0]["llm_enabled"] = "true"
    write_csv(results, FIELDS, rows)

    with pytest.raises(ValueError, match="LLM must remain disabled"):
        summarize(results, key, assignment)


def test_protocol_deviation_and_unresolved_outcome_are_recorded(tmp_path):
    key, assignment, results, assignments = study_files(tmp_path)
    rows = completed_rows(assignments)
    rows[0]["diagnosis"] = "unresolved"
    rows[0]["evidence_references"] = ""
    rows[0]["protocol_deviation"] = "Timer was briefly paused."
    write_csv(results, FIELDS, rows)

    report = summarize(results, key, assignment)

    assert report["conditions"]["manual"]["outcomes"]["unresolved"] == 1
    assert report["protocol_deviations"] == [{
        "trial_id": "p1-t1",
        "description": "Timer was briefly paused.",
    }]
    assert "Timer was briefly paused" in render_markdown(report)


def test_frozen_cases_assignments_and_template_are_consistent():
    root = Path(__file__).resolve().parents[1]
    with (root / "evaluation/impact_case_key_v1.csv").open(newline="") as source:
        frozen_key = {
            row["case_id"]: row["expected_category"]
            for row in csv.DictReader(source)
        }
    with (root / "evaluation/impact_cases_v1.csv").open(newline="") as source:
        frozen_cases = list(csv.DictReader(source))
    for case in frozen_cases:
        expected_rows = int(case["expected_rows"])
        actual_rows = int(case["actual_rows"])
        category, _, _ = classify_evidence(
            [case["log_message"]],
            max(expected_rows - actual_rows, 0),
            expected_rows,
            actual_rows,
        )
        assert category == frozen_key[case["case_id"]]

    with (root / "evaluation/impact_assignments_v1.csv").open(newline="") as source:
        frozen_assignments = list(csv.DictReader(source))
    with (root / "evaluation/impact_template.csv").open(newline="") as source:
        frozen_template = list(csv.DictReader(source))
    assert [
        tuple(row[field] for field in ASSIGNMENT_FIELDS)
        for row in frozen_template
    ] == [
        tuple(row[field] for field in ASSIGNMENT_FIELDS)
        for row in frozen_assignments
    ]
    assert len({row["trial_id"] for row in frozen_assignments}) == 40
    assert all(row["llm_enabled"] == "false" for row in frozen_template)
    participant_counts = Counter(
        (row["participant_id"], row["condition"])
        for row in frozen_assignments
    )
    case_counts = Counter(
        (row["case_id"], row["condition"])
        for row in frozen_assignments
    )
    assert all(
        participant_counts[(participant, "manual")] == 5
        and participant_counts[(participant, "opsintel")] == 5
        for participant in {row["participant_id"] for row in frozen_assignments}
    )
    assert all(
        case_counts[(case_id, "manual")] == 2
        and case_counts[(case_id, "opsintel")] == 2
        for case_id in frozen_key
    )
