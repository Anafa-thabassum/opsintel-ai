"""Summarize reviewer-recorded manual and OpsIntel investigation trials."""

import argparse
import csv
import json
import statistics
from pathlib import Path


CONDITIONS = {"manual", "opsintel"}
OUTCOMES = {"correct", "incorrect", "unresolved"}
BOOLEAN_VALUES = {"true": True, "false": False}


def _boolean(value, field, row_number):
    normalized = value.strip().lower()
    if normalized not in BOOLEAN_VALUES:
        raise ValueError(
            f"Row {row_number}: {field} must be true or false"
        )
    return BOOLEAN_VALUES[normalized]


def summarize(path):
    with Path(path).open(newline="") as source:
        rows = list(csv.DictReader(source))

    if not rows:
        raise ValueError("Impact study file contains no observations")

    parsed = []
    for row_number, row in enumerate(rows, start=2):
        condition = row["condition"].strip().lower()
        outcome = row["outcome"].strip().lower()
        if condition not in CONDITIONS:
            raise ValueError(f"Row {row_number}: unknown condition {condition}")
        if outcome not in OUTCOMES:
            raise ValueError(f"Row {row_number}: unknown outcome {outcome}")

        seconds = float(row["seconds"])
        if seconds <= 0:
            raise ValueError(f"Row {row_number}: seconds must be positive")

        parsed.append({
            "participant_id": row["participant_id"].strip(),
            "case_id": row["case_id"].strip(),
            "condition": condition,
            "seconds": seconds,
            "outcome": outcome,
            "cited_source": _boolean(
                row["cited_source"], "cited_source", row_number
            ),
            "unsafe_confirmation": _boolean(
                row["unsafe_confirmation"],
                "unsafe_confirmation",
                row_number,
            ),
        })

    condition_results = {}
    for condition in sorted(CONDITIONS):
        observations = [
            row for row in parsed if row["condition"] == condition
        ]
        if not observations:
            raise ValueError(f"No observations for condition: {condition}")

        outcome_counts = {
            outcome: sum(row["outcome"] == outcome for row in observations)
            for outcome in sorted(OUTCOMES)
        }
        condition_results[condition] = {
            "observations": len(observations),
            "median_seconds": round(statistics.median(
                row["seconds"] for row in observations
            ), 2),
            "outcomes": outcome_counts,
            "correct_pct": round(
                outcome_counts["correct"] * 100 / len(observations), 1
            ),
            "evidence_traceability_pct": round(
                sum(row["cited_source"] for row in observations)
                * 100
                / len(observations),
                1,
            ),
            "unsafe_confirmation_events": sum(
                row["unsafe_confirmation"] for row in observations
            ),
        }

    manual_seconds = condition_results["manual"]["median_seconds"]
    opsintel_seconds = condition_results["opsintel"]["median_seconds"]
    paired_keys = {
        (row["participant_id"], row["case_id"])
        for row in parsed
        if row["condition"] == "manual"
    } & {
        (row["participant_id"], row["case_id"])
        for row in parsed
        if row["condition"] == "opsintel"
    }

    return {
        "participants": len({row["participant_id"] for row in parsed}),
        "cases": len({row["case_id"] for row in parsed}),
        "paired_participant_cases": len(paired_keys),
        "conditions": condition_results,
        "median_time_saved_pct": round(
            (manual_seconds - opsintel_seconds) * 100 / manual_seconds,
            1,
        ),
        "scope": (
            "Reviewer-recorded study results; validity depends on the case "
            "selection, participant sample, and protocol compliance."
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="CSV copied from evaluation/impact_template.csv")
    args = parser.parse_args()
    print(json.dumps(summarize(args.path), indent=2))


if __name__ == "__main__":
    main()
