"""Validate and summarize the counterbalanced human impact study."""

import argparse
import csv
import hashlib
import json
import statistics
import subprocess
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_KEY = ROOT / "evaluation/impact_case_key_v1.csv"
DEFAULT_ASSIGNMENT = ROOT / "evaluation/impact_assignments_v1.csv"
CONDITIONS = {"manual", "opsintel"}
DIAGNOSES = {
    "timeout",
    "schema_mismatch",
    "dependency_failure",
    "early_termination",
    "incomplete_data",
    "unresolved",
}
BOOLEAN_VALUES = {"true": True, "false": False}
FIELDS = {
    "participant_id",
    "trial_order",
    "case_id",
    "condition",
    "seconds",
    "diagnosis",
    "source_reference",
    "confidence",
    "unsafe_confirmation",
}


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _boolean(value, field, row_number):
    normalized = value.strip().lower()
    if normalized not in BOOLEAN_VALUES:
        raise ValueError(f"Row {row_number}: {field} must be true or false")
    return BOOLEAN_VALUES[normalized]


def _read_csv(path, required_fields):
    with Path(path).open(newline="") as source:
        reader = csv.DictReader(source)
        missing = required_fields - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")
        return list(reader)


def _load_key(path):
    rows = _read_csv(path, {"case_id", "expected_category"})
    key = {}
    for row_number, row in enumerate(rows, start=2):
        case_id = row["case_id"].strip()
        expected = row["expected_category"].strip().lower()
        if not case_id or case_id in key:
            raise ValueError(f"Row {row_number}: blank or duplicate case_id")
        if expected not in DIAGNOSES - {"unresolved"}:
            raise ValueError(f"Row {row_number}: unknown expected category")
        key[case_id] = expected
    return key


def _load_assignment(path):
    rows = _read_csv(
        path,
        {"participant_id", "trial_order", "case_id", "condition"},
    )
    assignments = {}
    for row_number, row in enumerate(rows, start=2):
        participant_id = row["participant_id"].strip()
        case_id = row["case_id"].strip()
        condition = row["condition"].strip().lower()
        trial_order = int(row["trial_order"])
        key = (participant_id, case_id)
        if not participant_id or not case_id or key in assignments:
            raise ValueError(f"Row {row_number}: blank or duplicate assignment")
        if condition not in CONDITIONS or trial_order <= 0:
            raise ValueError(f"Row {row_number}: invalid assignment")
        assignments[key] = (trial_order, condition)
    return assignments


def _git_state():
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    dirty = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return commit, not bool(dirty)


def summarize(
    path,
    key_path=DEFAULT_KEY,
    assignment_path=DEFAULT_ASSIGNMENT,
    recruitment_path=None,
):
    rows = _read_csv(path, FIELDS)
    if not rows:
        raise ValueError("Impact study file contains no observations")

    expected_by_case = _load_key(key_path)
    assignments = _load_assignment(assignment_path)
    parsed = []
    observed = set()

    for row_number, row in enumerate(rows, start=2):
        participant_id = row["participant_id"].strip()
        case_id = row["case_id"].strip()
        condition = row["condition"].strip().lower()
        diagnosis = row["diagnosis"].strip().lower()
        key = (participant_id, case_id)

        required_values = ("seconds", "diagnosis", "confidence", "unsafe_confirmation")
        if any(not row[field].strip() for field in required_values):
            raise ValueError(f"Row {row_number}: incomplete measurement")
        if not participant_id or case_id not in expected_by_case:
            raise ValueError(f"Row {row_number}: unknown participant or case")
        if key not in assignments or key in observed:
            raise ValueError(f"Row {row_number}: unexpected or duplicate trial")
        if condition not in CONDITIONS or diagnosis not in DIAGNOSES:
            raise ValueError(f"Row {row_number}: invalid condition or diagnosis")

        trial_order = int(row["trial_order"])
        if (trial_order, condition) != assignments[key]:
            raise ValueError(f"Row {row_number}: trial does not match assignment")

        seconds = float(row["seconds"])
        confidence = int(row["confidence"])
        if seconds <= 0 or not 1 <= confidence <= 5:
            raise ValueError(f"Row {row_number}: invalid seconds or confidence")

        expected = expected_by_case[case_id]
        outcome = (
            "unresolved"
            if diagnosis == "unresolved"
            else "correct" if diagnosis == expected else "incorrect"
        )
        observed.add(key)
        parsed.append({
            "participant_id": participant_id,
            "case_id": case_id,
            "condition": condition,
            "seconds": seconds,
            "outcome": outcome,
            "cited_source": bool(row["source_reference"].strip()),
            "confidence": confidence,
            "unsafe_confirmation": _boolean(
                row["unsafe_confirmation"],
                "unsafe_confirmation",
                row_number,
            ),
        })

    missing_trials = set(assignments) - observed
    if missing_trials:
        raise ValueError(f"Impact study is incomplete: {len(missing_trials)} trials missing")

    condition_results = {}
    for condition in sorted(CONDITIONS):
        observations = [row for row in parsed if row["condition"] == condition]
        outcome_counts = {
            outcome: sum(row["outcome"] == outcome for row in observations)
            for outcome in ("correct", "incorrect", "unresolved")
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
                * 100 / len(observations),
                1,
            ),
            "median_confidence": statistics.median(
                row["confidence"] for row in observations
            ),
            "unsafe_confirmation_events": sum(
                row["unsafe_confirmation"] for row in observations
            ),
        }

    manual = condition_results["manual"]
    opsintel = condition_results["opsintel"]
    time_saved_pct = round(
        (manual["median_seconds"] - opsintel["median_seconds"])
        * 100 / manual["median_seconds"],
        1,
    )
    thresholds = {
        "median_time_saved_at_least_30_pct": time_saved_pct >= 30,
        "diagnosis_agreement_not_lower": (
            opsintel["correct_pct"] >= manual["correct_pct"]
        ),
        "assisted_traceability_at_least_90_pct": (
            opsintel["evidence_traceability_pct"] >= 90
        ),
        "zero_assisted_unsafe_confirmations": (
            opsintel["unsafe_confirmation_events"] == 0
        ),
    }

    participant_counts = Counter(
        (row["participant_id"], row["condition"]) for row in parsed
    )
    case_counts = Counter((row["case_id"], row["condition"]) for row in parsed)
    participants = {row["participant_id"] for row in parsed}
    cases = {row["case_id"] for row in parsed}
    design_checks = {
        "at_least_four_participants": len(participants) >= 4,
        "ten_cases": len(cases) == 10,
        "balanced_conditions_per_participant": all(
            participant_counts[(participant, "manual")]
            == participant_counts[(participant, "opsintel")]
            for participant in participants
        ),
        "balanced_conditions_per_case": all(
            case_counts[(case_id, "manual")]
            == case_counts[(case_id, "opsintel")]
            for case_id in cases
        ),
    }
    commit, clean = _git_state()

    recruitment = (
        Path(recruitment_path).read_text().strip()
        if recruitment_path
        else "Not recorded in this test run."
    )
    return {
        "evaluation": "counterbalanced-human-impact-study-v1",
        "results_file": Path(path).name,
        "results_sha256": _sha256(path),
        "case_key_sha256": _sha256(key_path),
        "assignment_sha256": _sha256(assignment_path),
        "tested_commit": commit,
        "working_tree_clean": clean,
        "participants": len(participants),
        "cases": len(cases),
        "observations": len(parsed),
        "conditions": condition_results,
        "median_time_saved_pct": time_saved_pct,
        "diagnosis_agreement_delta_points": round(
            opsintel["correct_pct"] - manual["correct_pct"], 1
        ),
        "design_checks": design_checks,
        "success_thresholds": thresholds,
        "study_target_met": all(design_checks.values()) and all(thresholds.values()),
        "recruitment_description": recruitment,
        "scope": (
            "Small counterbalanced study on synthetic incidents; results do "
            "not establish production impact or independent LLM quality."
        ),
    }


def render_markdown(report):
    manual = report["conditions"]["manual"]
    opsintel = report["conditions"]["opsintel"]
    verdict = (
        "The predefined study target was met."
        if report["study_target_met"]
        else "The predefined study target was not met; report the mixed or negative result without a time-saving claim."
    )
    return "\n".join([
        "# OpsIntel AI impact study v1",
        "",
        f"- Participants: **{report['participants']}**",
        f"- Cases: **{report['cases']}**",
        f"- Completed observations: **{report['observations']}**",
        f"- Tested commit: `{report['tested_commit']}`",
        "",
        "## Results",
        "",
        "| Metric | Manual | OpsIntel AI |",
        "|---|---:|---:|",
        f"| Median diagnosis time | {manual['median_seconds']} s | {opsintel['median_seconds']} s |",
        f"| Correct diagnoses | {manual['correct_pct']}% | {opsintel['correct_pct']}% |",
        f"| Evidence traceability | {manual['evidence_traceability_pct']}% | {opsintel['evidence_traceability_pct']}% |",
        f"| Unsafe confirmation events | {manual['unsafe_confirmation_events']} | {opsintel['unsafe_confirmation_events']} |",
        "",
        f"Median time difference: **{report['median_time_saved_pct']}%** (positive means OpsIntel was faster).",
        f"Diagnosis agreement difference: **{report['diagnosis_agreement_delta_points']} percentage points**.",
        "",
        "## Interpretation",
        "",
        verdict,
        "",
        "## Recruitment",
        "",
        report["recruitment_description"],
        "",
        "## Scope",
        "",
        report["scope"],
        "",
    ])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Completed impact-study CSV")
    parser.add_argument("--key", default=DEFAULT_KEY)
    parser.add_argument("--assignment", default=DEFAULT_ASSIGNMENT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--recruitment", type=Path, required=True)
    args = parser.parse_args()
    result = summarize(
        args.path,
        args.key,
        args.assignment,
        args.recruitment,
    )
    rendered = json.dumps(result, indent=2)
    print(rendered)
    if args.output:
        args.output.write_text(rendered + "\n")
    if args.markdown_output:
        args.markdown_output.write_text(render_markdown(result))


if __name__ == "__main__":
    main()
