import csv

import pytest

from scripts.summarize_impact_study import summarize


FIELDS = [
    "participant_id",
    "case_id",
    "condition",
    "seconds",
    "outcome",
    "cited_source",
    "unsafe_confirmation",
]


def write_study(path, rows):
    with path.open("w", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def test_impact_summary_reports_time_outcomes_and_safety(tmp_path):
    path = tmp_path / "impact.csv"
    write_study(path, [
        {
            "participant_id": "p1",
            "case_id": "c1",
            "condition": "manual",
            "seconds": "120",
            "outcome": "correct",
            "cited_source": "false",
            "unsafe_confirmation": "false",
        },
        {
            "participant_id": "p1",
            "case_id": "c1",
            "condition": "opsintel",
            "seconds": "60",
            "outcome": "correct",
            "cited_source": "true",
            "unsafe_confirmation": "false",
        },
    ])

    result = summarize(path)

    assert result["median_time_saved_pct"] == 50.0
    assert result["paired_participant_cases"] == 1
    assert result["conditions"]["opsintel"]["correct_pct"] == 100.0
    assert result["conditions"]["opsintel"]["evidence_traceability_pct"] == 100.0


def test_impact_summary_rejects_invalid_boolean(tmp_path):
    path = tmp_path / "impact.csv"
    write_study(path, [
        {
            "participant_id": "p1",
            "case_id": "c1",
            "condition": "manual",
            "seconds": "30",
            "outcome": "unresolved",
            "cited_source": "maybe",
            "unsafe_confirmation": "false",
        }
    ])

    with pytest.raises(ValueError, match="cited_source"):
        summarize(path)
