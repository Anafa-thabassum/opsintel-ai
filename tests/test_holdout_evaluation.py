import csv
import json
from pathlib import Path

from scripts.evaluate_holdout import evaluate


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
