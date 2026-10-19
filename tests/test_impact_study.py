import csv
from collections import Counter
from pathlib import Path

import pytest

from app.investigator import classify_evidence
from scripts.summarize_impact_study import render_markdown, summarize


FIELDS = [
    "participant_id",
    "trial_order",
    "case_id",
    "condition",
    "seconds",
    "diagnosis",
    "source_reference",
    "confidence",
    "unsafe_confirmation",
]


def write_csv(path, fields, rows):
    with path.open("w", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def test_impact_summary_validates_design_and_derives_outcomes(tmp_path):
    key = tmp_path / "key.csv"
    assignment = tmp_path / "assignment.csv"
    results = tmp_path / "results.csv"
    write_csv(key, ["case_id", "expected_category"], [
        {"case_id": "c1", "expected_category": "timeout"},
        {"case_id": "c2", "expected_category": "schema_mismatch"},
    ])
    write_csv(
        assignment,
        ["participant_id", "trial_order", "case_id", "condition"],
        [
            {"participant_id": "p1", "trial_order": 1, "case_id": "c1", "condition": "manual"},
            {"participant_id": "p1", "trial_order": 2, "case_id": "c2", "condition": "opsintel"},
            {"participant_id": "p2", "trial_order": 1, "case_id": "c1", "condition": "opsintel"},
            {"participant_id": "p2", "trial_order": 2, "case_id": "c2", "condition": "manual"},
        ],
    )
    common = {"source_reference": "LOG-1", "confidence": 4, "unsafe_confirmation": "false"}
    write_csv(results, FIELDS, [
        {**common, "participant_id": "p1", "trial_order": 1, "case_id": "c1", "condition": "manual", "seconds": 120, "diagnosis": "timeout"},
        {**common, "participant_id": "p1", "trial_order": 2, "case_id": "c2", "condition": "opsintel", "seconds": 60, "diagnosis": "schema_mismatch"},
        {**common, "participant_id": "p2", "trial_order": 1, "case_id": "c1", "condition": "opsintel", "seconds": 50, "diagnosis": "timeout"},
        {**common, "participant_id": "p2", "trial_order": 2, "case_id": "c2", "condition": "manual", "seconds": 100, "diagnosis": "schema_mismatch"},
    ])

    result = summarize(results, key, assignment)

    assert result["median_time_saved_pct"] == 50.0
    assert result["conditions"]["opsintel"]["correct_pct"] == 100.0
    assert result["conditions"]["opsintel"]["evidence_traceability_pct"] == 100.0
    assert result["design_checks"]["balanced_conditions_per_case"] is True
    assert result["study_target_met"] is False
    assert "not met" in render_markdown(result)

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
    assignment_fields = ("participant_id", "trial_order", "case_id", "condition")
    assert [tuple(row[field] for field in assignment_fields) for row in frozen_template] == [
        tuple(row[field] for field in assignment_fields)
        for row in frozen_assignments
    ]
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


def test_impact_summary_rejects_invalid_boolean(tmp_path):
    key = tmp_path / "key.csv"
    assignment = tmp_path / "assignment.csv"
    results = tmp_path / "results.csv"
    write_csv(key, ["case_id", "expected_category"], [
        {"case_id": "c1", "expected_category": "timeout"},
    ])
    write_csv(
        assignment,
        ["participant_id", "trial_order", "case_id", "condition"],
        [{"participant_id": "p1", "trial_order": 1, "case_id": "c1", "condition": "manual"}],
    )
    write_csv(results, FIELDS, [{
        "participant_id": "p1",
        "trial_order": 1,
        "case_id": "c1",
        "condition": "manual",
        "seconds": 30,
        "diagnosis": "unresolved",
        "source_reference": "",
        "confidence": 2,
        "unsafe_confirmation": "maybe",
    }])

    with pytest.raises(ValueError, match="unsafe_confirmation"):
        summarize(results, key, assignment)
