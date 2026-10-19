"""Evaluate frozen holdout cases without changing the classifier."""

import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path

from app.investigator import classify_evidence


VALID_CATEGORIES = {
    "conflicting_evidence",
    "delayed_run",
    "dependency_failure",
    "duplicate_data",
    "early_termination",
    "incomplete_data",
    "schema_mismatch",
    "timeout",
    "unclassified",
}


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _git_commit(repo_root):
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        check=False,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def _optional_int(row, name):
    value = row.get(name, "").strip()
    return int(value) if value else None


def evaluate(path):
    path = Path(path)
    with path.open(newline="") as source:
        cases = list(csv.DictReader(source))

    if not cases:
        raise ValueError("Holdout file contains no cases")

    results = []
    seen_ids = set()
    for row in cases:
        case_id = row["id"].strip()
        if not case_id or case_id in seen_ids:
            raise ValueError(f"Missing or duplicate case id: {case_id!r}")
        seen_ids.add(case_id)

        expected = row["expected"].strip()
        if expected not in VALID_CATEGORIES:
            raise ValueError(f"Unknown expected category: {expected}")

        logs = json.loads(row["logs_json"])
        if not isinstance(logs, list) or not logs or not all(
            isinstance(log, str) and log.strip() for log in logs
        ):
            raise ValueError(f"Case {case_id} must contain non-empty log strings")

        expected_rows = _optional_int(row, "expected_rows")
        actual_rows = _optional_int(row, "actual_rows")
        if (expected_rows is None) != (actual_rows is None):
            raise ValueError(
                f"Case {case_id} must provide both expected_rows and actual_rows"
            )

        predicted, _, _ = classify_evidence(
            logs,
            int(row["missing_rows"]),
            expected_rows,
            actual_rows,
        )
        results.append({
            "id": case_id,
            "expected": expected,
            "predicted": predicted,
            "correct": predicted == expected,
        })

    correct = sum(result["correct"] for result in results)
    category_results = {}
    for result in results:
        category = category_results.setdefault(
            result["expected"], {"correct": 0, "total": 0}
        )
        category["correct"] += int(result["correct"])
        category["total"] += 1

    repo_root = Path(__file__).resolve().parents[1]
    return {
        "evaluation": "frozen-synthetic-holdout-v1",
        "dataset_file": path.name,
        "dataset_sha256": _sha256(path),
        "classifier_file": "app/investigator.py",
        "classifier_sha256": _sha256(repo_root / "app" / "investigator.py"),
        "classifier_commit": _git_commit(repo_root),
        "correct": correct,
        "total": len(results),
        "accuracy_pct": round(correct * 100 / len(results), 1),
        "category_results": dict(sorted(category_results.items())),
        "scope": (
            "Project-authored synthetic holdout frozen before execution; "
            "not an independent or production accuracy estimate."
        ),
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Frozen holdout CSV")
    parser.add_argument("--output", help="Optional JSON report path")
    args = parser.parse_args()
    report = json.dumps(evaluate(args.path), indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(report)
    print(report, end="")


if __name__ == "__main__":
    main()
