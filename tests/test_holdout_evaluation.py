import csv
import json
from pathlib import Path

import pytest

from scripts.evaluate_holdout import evaluate, render_markdown


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
        "classifier_sha256",
        "correct",
        "total",
        "accuracy_pct",
        "category_results",
        "results",
    ):
        assert frozen[key] == published[key]


def test_independent_holdout_requires_authors_and_frozen_ref(tmp_path, monkeypatch):
    path = tmp_path / "independent.csv"
    with path.open("w", newline="") as destination:
        writer = csv.writer(destination)
        writer.writerow([
            "id", "logs_json", "missing_rows", "expected_rows",
            "actual_rows", "expected", "author_id",
        ])
        for index in range(15):
            writer.writerow([
                f"external-{index + 1}",
                json.dumps(["Execution deadline exceeded"]),
                0,
                100,
                100,
                "timeout",
                "R1" if index % 2 == 0 else "R2",
            ])
    monkeypatch.setattr(
        "scripts.evaluate_holdout._validate_independent_freeze",
        lambda *_: {
            "frozen_ref": "independent-v1",
            "frozen_commit": "abc123",
            "dataset_frozen_sha256": "dataset",
            "classifier_frozen_sha256": "classifier",
        },
    )

    result = evaluate(path, "independent", "independent-v1")

    assert result["provenance"] == "independent"
    assert result["author_ids"] == ["R1", "R2"]
    assert result["correct"] == 15
    rendered = render_markdown(result)
    assert "No misses occurred" in rendered
    assert "not establish production accuracy" in rendered


def test_independent_holdout_rejects_missing_freeze(tmp_path):
    path = tmp_path / "too-small.csv"
    with path.open("w", newline="") as destination:
        writer = csv.writer(destination)
        writer.writerow(["id", "logs_json", "missing_rows", "expected", "author_id"])
        writer.writerow(["external-1", json.dumps(["timed out"]), 0, "timeout", "R1"])

    with pytest.raises(ValueError, match="15 to 20"):
        evaluate(path, "independent")
