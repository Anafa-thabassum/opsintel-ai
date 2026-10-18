"""Evaluate reviewer-provided holdout cases without changing the classifier."""

import argparse
import csv
import json
from pathlib import Path

from app.investigator import classify_evidence


VALID_CATEGORIES = {
    "dependency_failure",
    "early_termination",
    "incomplete_data",
    "schema_mismatch",
    "timeout",
    "unclassified",
}


def evaluate(path):
    with Path(path).open(newline="") as source:
        cases = list(csv.DictReader(source))

    if not cases:
        raise ValueError("Holdout file contains no cases")

    results = []
    for row in cases:
        expected = row["expected"].strip()
        if expected not in VALID_CATEGORIES:
            raise ValueError(f"Unknown expected category: {expected}")

        logs = json.loads(row["logs_json"])
        predicted, _, _ = classify_evidence(logs, int(row["missing_rows"]))
        results.append({
            "id": row["id"],
            "expected": expected,
            "predicted": predicted,
            "correct": predicted == expected,
        })

    correct = sum(result["correct"] for result in results)
    return {
        "correct": correct,
        "total": len(results),
        "accuracy_pct": round(correct * 100 / len(results), 1),
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="CSV copied from evaluation/holdout_template.csv")
    args = parser.parse_args()
    print(json.dumps(evaluate(args.path), indent=2))


if __name__ == "__main__":
    main()
