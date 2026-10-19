import csv
import json
from pathlib import Path

import pytest

from scripts.evaluate_holdout import evaluate, render_markdown


INDEPENDENT_FIELDS = [
    "dataset_version",
    "id",
    "evidence_json",
    "missing_rows",
    "expected_rows",
    "actual_rows",
    "expected",
    "expected_findings_json",
    "expected_uncertainty",
    "author_id",
    "reviewer_provenance",
]


def independent_rows():
    return [
        {
            "dataset_version": "independent-v1",
            "id": f"external-{index + 1}",
            "evidence_json": json.dumps([{
                "reference": f"LOG-{index + 1}",
                "observation": "Execution deadline exceeded",
            }]),
            "missing_rows": "0",
            "expected_rows": "100",
            "actual_rows": "100",
            "expected": "timeout",
            "expected_findings_json": json.dumps([
                "Execution exceeded a configured limit"
            ]),
            "expected_uncertainty": "candidate_only",
            "author_id": "R1" if index % 2 == 0 else "R2",
            "reviewer_provenance": "external-reviewer",
        }
        for index in range(15)
    ]


def write_independent(path, rows=None, fields=None):
    with path.open("w", newline="") as destination:
        writer = csv.DictWriter(
            destination,
            fieldnames=fields or INDEPENDENT_FIELDS,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(independent_rows() if rows is None else rows)


def stub_freeze(monkeypatch):
    monkeypatch.setattr(
        "scripts.evaluate_holdout._validate_independent_freeze",
        lambda *_: {
            "frozen_ref": "independent-v1",
            "frozen_commit": "abc123",
            "dataset_frozen_sha256": "dataset",
            "classifier_frozen_sha256": "classifier",
            "evaluator_frozen_sha256": "evaluator",
        },
    )


def test_reviewer_holdout_file_is_scored(tmp_path):
    path = tmp_path / "holdout.csv"
    with path.open("w", newline="") as destination:
        writer = csv.writer(destination)
        writer.writerow(["id", "logs_json", "missing_rows", "expected"])
        writer.writerow([
            "hidden-1",
            json.dumps(["Execution deadline exceeded"]),
            0,
            "timeout",
        ])

    result = evaluate(path)

    assert result["accuracy_pct"] == 100.0
    assert result["results"][0]["correct"] is True

    repo_root = Path(__file__).resolve().parents[1]
    frozen = evaluate(repo_root / "evaluation" / "frozen_holdout_v1.csv")
    published = json.loads(
        (repo_root / "reports" / "frozen-holdout-v1.json").read_text()
    )
    for key in (
        "dataset_sha256",
        "correct",
        "total",
        "accuracy_pct",
        "category_results",
        "results",
    ):
        assert frozen[key] == published[key]
    assert len(published["classifier_sha256"]) == 64


def test_independent_holdout_requires_authors_and_frozen_ref(tmp_path, monkeypatch):
    path = tmp_path / "independent.csv"
    write_independent(path)
    stub_freeze(monkeypatch)

    result = evaluate(
        path,
        "independent",
        "independent-v1",
        "2026-10-19T12:00:00+00:00",
    )

    assert result["provenance"] == "independent"
    assert result["author_ids"] == ["R1", "R2"]
    assert result["correct"] == 15
    assert result["completed_cases"] == 15
    assert result["missing_labels"] == 0
    assert result["traceable_cases"] == 15
    assert result["independent_validation_status"] == "complete"
    assert result["classifier_configuration_version"] == (
        "deterministic-default-v1"
    )
    rendered = render_markdown(result)
    assert "No misses occurred" in rendered
    assert "not establish production accuracy" in rendered


def test_independent_holdout_rejects_missing_freeze(tmp_path):
    path = tmp_path / "independent.csv"
    write_independent(path)

    with pytest.raises(ValueError, match="requires --frozen-ref"):
        evaluate(path, "independent")


def test_error_analysis_records_inputs_and_a_fix_for_each_miss(tmp_path):
    path = tmp_path / "miss.csv"
    with path.open("w", newline="") as destination:
        writer = csv.writer(destination)
        writer.writerow([
            "id", "logs_json", "missing_rows", "expected_rows",
            "actual_rows", "expected",
        ])
        writer.writerow([
            "miss-1", json.dumps(["Execution deadline exceeded"]), 0,
            100, 100, "schema_mismatch",
        ])

    result = evaluate(path)
    rendered = render_markdown(result)

    assert result["results"][0]["inputs"]["logs"] == [
        "Execution deadline exceeded"
    ]
    assert "miss-1" in rendered
    assert "schema_mismatch" in rendered
    assert "timeout" in rendered
    assert "Evidence reviewed" in rendered
    assert "smallest rule or abstention test" in rendered


def test_independent_template_is_separate_and_empty():
    root = Path(__file__).resolve().parents[1]
    template = root / "evaluation" / "holdout_template.csv"
    development = root / "evaluation" / "frozen_holdout_v1.csv"

    with template.open(newline="") as source:
        template_reader = csv.DictReader(source)
        assert template_reader.fieldnames == INDEPENDENT_FIELDS
        assert list(template_reader) == []
    assert template != development
    assert "evidence_json" not in development.read_text().splitlines()[0]


def test_independent_holdout_rejects_incomplete_schema(tmp_path):
    path = tmp_path / "invalid.csv"
    fields = [
        field for field in INDEPENDENT_FIELDS
        if field != "expected_findings_json"
    ]
    write_independent(path, fields=fields)

    with pytest.raises(ValueError, match="expected_findings_json"):
        evaluate(path, "independent", "independent-v1")


def test_independent_holdout_rejects_invalid_evidence_schema(tmp_path):
    path = tmp_path / "invalid-evidence.csv"
    rows = independent_rows()
    rows[0]["evidence_json"] = json.dumps([{
        "observation": "Execution deadline exceeded",
    }])
    write_independent(path, rows)

    with pytest.raises(ValueError, match="evidence without a reference"):
        evaluate(path, "independent", "independent-v1")


def test_independent_holdout_rejects_duplicate_ids(tmp_path):
    path = tmp_path / "duplicate.csv"
    rows = independent_rows()
    rows[1]["id"] = rows[0]["id"]
    write_independent(path, rows)

    with pytest.raises(ValueError, match="duplicate case id"):
        evaluate(path, "independent", "independent-v1")


def test_missing_label_is_reported_without_validation_claim(
    tmp_path,
    monkeypatch,
):
    path = tmp_path / "missing-label.csv"
    rows = independent_rows()
    rows[0]["expected"] = ""
    rows[0]["expected_findings_json"] = ""
    rows[0]["expected_uncertainty"] = ""
    write_independent(path, rows)
    stub_freeze(monkeypatch)

    result = evaluate(path, "independent", "independent-v1")

    assert result["completed_cases"] == 14
    assert result["missing_labels"] == 1
    assert result["independent_validation_status"] == "pending"
    assert result["results"][0]["outcome"] == "missing_label"
    assert "external-1" in render_markdown(result)


def test_correct_incorrect_and_unresolved_outcomes(tmp_path, monkeypatch):
    path = tmp_path / "outcomes.csv"
    rows = independent_rows()
    rows[1]["expected"] = "schema_mismatch"
    rows[2]["evidence_json"] = json.dumps([{
        "reference": "LOG-3",
        "observation": "Worker emitted opaque code ZX-41",
    }])
    write_independent(path, rows)
    stub_freeze(monkeypatch)

    result = evaluate(path, "independent", "independent-v1")

    assert result["correct_findings"] == 13
    assert result["incorrect_findings"] == 2
    assert result["unresolved_cases"] == 1
    assert result["results"][0]["outcome"] == "correct"
    assert result["results"][1]["outcome"] == "incorrect"
    assert result["results"][2]["resolution_status"] == "unresolved"


def test_scoring_and_report_are_reproducible(tmp_path, monkeypatch):
    path = tmp_path / "repeatable.csv"
    write_independent(path)
    stub_freeze(monkeypatch)
    timestamp = "2026-10-19T12:00:00+00:00"

    first = evaluate(path, "independent", "independent-v1", timestamp)
    second = evaluate(path, "independent", "independent-v1", timestamp)

    assert first == second
    assert render_markdown(first) == render_markdown(second)


def test_missing_reviewer_provenance_cannot_claim_independence(tmp_path):
    path = tmp_path / "missing-provenance.csv"
    rows = independent_rows()
    rows[0]["reviewer_provenance"] = ""
    write_independent(path, rows)

    with pytest.raises(ValueError, match="lacks external reviewer provenance"):
        evaluate(path, "independent", "independent-v1")
