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
}
MEASUREMENT_FIELDS = (
    "seconds",
    "diagnosis",
    "confidence",
    "unsafe_confirmation",
)


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _boolean(value, field, row_number):
    normalized = value.strip().lower()
    if normalized not in BOOLEAN_VALUES:
        raise ValueError(f"Row {row_number}: {field} must be true or false")
    return BOOLEAN_VALUES[normalized]


def _positive_integer(value, field, row_number):
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Row {row_number}: {field} must be a positive integer") from exc
    if number <= 0:
        raise ValueError(f"Row {row_number}: {field} must be a positive integer")
    return number


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
        {"trial_id", "participant_id", "trial_order", "case_id", "condition"},
    )
    assignments = {}
    participant_cases = set()
    participant_orders = set()
    for row_number, row in enumerate(rows, start=2):
        trial_id = row["trial_id"].strip()
        participant_id = row["participant_id"].strip()
        case_id = row["case_id"].strip()
        condition = row["condition"].strip().lower()
        trial_order = _positive_integer(row["trial_order"], "trial_order", row_number)
        participant_case = (participant_id, case_id)
        participant_order = (participant_id, trial_order)
        if not trial_id or not participant_id or not case_id:
            raise ValueError(f"Row {row_number}: blank assignment identifier")
        if (
            trial_id in assignments
            or participant_case in participant_cases
            or participant_order in participant_orders
        ):
            raise ValueError(f"Row {row_number}: duplicate assignment")
        if condition not in CONDITIONS:
            raise ValueError(f"Row {row_number}: invalid assignment condition")
        assignments[trial_id] = {
            "participant_id": participant_id,
            "trial_order": trial_order,
            "case_id": case_id,
            "condition": condition,
        }
        participant_cases.add(participant_case)
        participant_orders.add(participant_order)
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


def _condition_summary(rows, publish_metrics):
    outcomes = {
        outcome: sum(row["outcome"] == outcome for row in rows)
        for outcome in ("correct", "incorrect", "unresolved")
    }
    summary = {
        "observations": len(rows),
        "outcomes": outcomes,
        "median_seconds": None,
        "correct_pct": None,
        "evidence_traceability_pct": None,
        "median_confidence": None,
        "unsafe_confirmation_events": None,
    }
    if not publish_metrics:
        return summary
    summary.update({
        "median_seconds": round(
            statistics.median(row["seconds"] for row in rows), 2
        ),
        "correct_pct": round(outcomes["correct"] * 100 / len(rows), 1),
        "evidence_traceability_pct": round(
            sum(row["cited_source"] for row in rows) * 100 / len(rows),
            1,
        ),
        "median_confidence": statistics.median(
            row["confidence"] for row in rows
        ),
        "unsafe_confirmation_events": sum(
            row["unsafe_confirmation"] for row in rows
        ),
    })
    return summary


def summarize(
    path,
    key_path=DEFAULT_KEY,
    assignment_path=DEFAULT_ASSIGNMENT,
    recruitment_path=None,
):
    rows = _read_csv(path, FIELDS)
    expected_by_case = _load_key(key_path)
    assignments = _load_assignment(assignment_path)
    completed = []
    pending = []
    incomplete = []
    deviations = []
    observed_trial_ids = set()

    for row_number, row in enumerate(rows, start=2):
        trial_id = row["trial_id"].strip()
        if not trial_id or trial_id in observed_trial_ids:
            raise ValueError(f"Row {row_number}: blank or duplicate trial_id")
        if trial_id not in assignments:
            raise ValueError(f"Row {row_number}: unexpected trial_id")
        observed_trial_ids.add(trial_id)

        assignment = assignments[trial_id]
        trial_order = _positive_integer(row["trial_order"], "trial_order", row_number)
        actual_assignment = {
            "participant_id": row["participant_id"].strip(),
            "trial_order": trial_order,
            "case_id": row["case_id"].strip(),
            "condition": row["condition"].strip().lower(),
        }
        if actual_assignment != assignment:
            raise ValueError(f"Row {row_number}: trial does not match assignment")
        if assignment["case_id"] not in expected_by_case:
            raise ValueError(f"Row {row_number}: case is absent from the ground-truth key")
        if _boolean(row["llm_enabled"], "llm_enabled", row_number):
            raise ValueError(f"Row {row_number}: LLM must remain disabled")

        measurement_values = [row[field].strip() for field in MEASUREMENT_FIELDS]
        deviation = row["protocol_deviation"].strip()
        if deviation:
            deviations.append({"trial_id": trial_id, "description": deviation})
        if not any(measurement_values):
            pending.append(trial_id)
            continue
        if not all(measurement_values):
            incomplete.append(trial_id)
            continue

        diagnosis = row["diagnosis"].strip().lower()
        if diagnosis not in DIAGNOSES:
            raise ValueError(f"Row {row_number}: invalid diagnosis")
        try:
            seconds = float(row["seconds"])
        except ValueError as exc:
            raise ValueError(f"Row {row_number}: seconds must be a positive number") from exc
        if not 0 < seconds < float("inf"):
            raise ValueError(f"Row {row_number}: seconds must be a positive number")
        confidence = _positive_integer(row["confidence"], "confidence", row_number)
        if confidence > 5:
            raise ValueError(f"Row {row_number}: confidence must be between 1 and 5")

        expected = expected_by_case[assignment["case_id"]]
        outcome = (
            "unresolved"
            if diagnosis == "unresolved"
            else "correct" if diagnosis == expected else "incorrect"
        )
        completed.append({
            "trial_id": trial_id,
            **assignment,
            "seconds": seconds,
            "outcome": outcome,
            "cited_source": bool(row["evidence_references"].strip()),
            "confidence": confidence,
            "unsafe_confirmation": _boolean(
                row["unsafe_confirmation"],
                "unsafe_confirmation",
                row_number,
            ),
        })

    pending.extend(sorted(set(assignments) - observed_trial_ids))
    participant_counts = Counter(
        (item["participant_id"], item["condition"])
        for item in assignments.values()
    )
    case_counts = Counter(
        (item["case_id"], item["condition"])
        for item in assignments.values()
    )
    participants = {item["participant_id"] for item in assignments.values()}
    cases = {item["case_id"] for item in assignments.values()}
    design_checks = {
        "exactly_four_participants": len(participants) == 4,
        "exactly_ten_cases": len(cases) == 10,
        "exactly_forty_trials": len(assignments) == 40,
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
    complete_dataset = (
        len(completed) == len(assignments) and not pending and not incomplete
    )
    completed_conditions = Counter(row["condition"] for row in completed)
    comparison_ready = (
        complete_dataset
        and completed_conditions["manual"] > 0
        and completed_conditions["opsintel"] > 0
        and design_checks["balanced_conditions_per_participant"]
        and design_checks["balanced_conditions_per_case"]
    )
    condition_results = {
        condition: _condition_summary(
            [row for row in completed if row["condition"] == condition],
            comparison_ready,
        )
        for condition in sorted(CONDITIONS)
    }

    time_difference_pct = None
    agreement_delta = None
    thresholds = None
    if comparison_ready:
        manual = condition_results["manual"]
        opsintel = condition_results["opsintel"]
        time_difference_pct = round(
            (manual["median_seconds"] - opsintel["median_seconds"])
            * 100 / manual["median_seconds"],
            1,
        )
        agreement_delta = round(
            opsintel["correct_pct"] - manual["correct_pct"], 1
        )
        thresholds = {
            "median_time_difference_at_least_30_pct": time_difference_pct >= 30,
            "diagnosis_agreement_not_lower": agreement_delta >= 0,
            "assisted_traceability_at_least_90_pct": (
                opsintel["evidence_traceability_pct"] >= 90
            ),
            "zero_assisted_unsafe_confirmations": (
                opsintel["unsafe_confirmation_events"] == 0
            ),
        }

    study_target_met = (
        comparison_ready
        and all(design_checks.values())
        and all(thresholds.values())
    )
    commit, clean = _git_state()
    recruitment = (
        Path(recruitment_path).read_text().strip()
        if recruitment_path
        else "Not recorded."
    )
    return {
        "evaluation": "counterbalanced-human-impact-study-v1",
        "analysis_version": "2.0",
        "study_status": "complete" if complete_dataset else "pending",
        "llm_enabled": False,
        "results_file": Path(path).name,
        "results_sha256": _sha256(path),
        "case_key_sha256": _sha256(key_path),
        "assignment_sha256": _sha256(assignment_path),
        "tested_commit": commit,
        "working_tree_clean": clean,
        "planned_participants": len(participants),
        "planned_cases": len(cases),
        "assigned_trials": len(assignments),
        "completed_trials": len(completed),
        "pending_trials": len(pending),
        "pending_trial_ids": sorted(pending),
        "incomplete_trials": len(incomplete),
        "incomplete_trial_ids": sorted(incomplete),
        "protocol_deviations": deviations,
        "conditions": condition_results,
        "comparison_ready": comparison_ready,
        "median_time_difference_pct": time_difference_pct,
        "diagnosis_agreement_delta_points": agreement_delta,
        "design_checks": design_checks,
        "success_thresholds": thresholds,
        "study_target_met": study_target_met,
        "time_saving_claim_supported": study_target_met,
        "causal_impact_claim_supported": False,
        "recruitment_description": recruitment,
        "limitations": [
            "Synthetic incidents and a four-person convenience sample cannot establish production or causal impact.",
            "No comparison or time-saving claim is generated until all assigned trials are complete.",
            "The optional LLM is disabled; this study evaluates the deterministic workflow only.",
        ],
    }


def _display(value, suffix=""):
    return "Pending" if value is None else f"{value}{suffix}"


def render_markdown(report):
    manual = report["conditions"]["manual"]
    opsintel = report["conditions"]["opsintel"]
    if report["study_status"] == "pending":
        interpretation = (
            "The study has not been completed. No measured improvement or "
            "time-saving claim is available."
        )
    elif report["study_target_met"]:
        interpretation = (
            "The predefined target was met in this small synthetic study. "
            "This is an observed association, not a causal or production claim."
        )
    else:
        interpretation = (
            "The predefined target was not met. Report the mixed or negative "
            "result without a time-saving claim."
        )
    lines = [
        "# OpsIntel AI impact study v1",
        "",
        f"- Status: **{report['study_status']}**",
        f"- Planned participants: **{report['planned_participants']}**",
        f"- Assigned trials: **{report['assigned_trials']}**",
        f"- Completed trials: **{report['completed_trials']}**",
        f"- Pending trials: **{report['pending_trials']}**",
        f"- Incomplete trials: **{report['incomplete_trials']}**",
        "- Optional LLM: **disabled**",
        f"- Tested commit: `{report['tested_commit']}`",
        "",
        "## Results",
        "",
        "| Metric | Manual | OpsIntel AI |",
        "|---|---:|---:|",
        f"| Completed observations | {manual['observations']} | {opsintel['observations']} |",
        f"| Median diagnosis time | {_display(manual['median_seconds'], ' s')} | {_display(opsintel['median_seconds'], ' s')} |",
        f"| Correct diagnoses | {_display(manual['correct_pct'], '%')} | {_display(opsintel['correct_pct'], '%')} |",
        f"| Evidence traceability | {_display(manual['evidence_traceability_pct'], '%')} | {_display(opsintel['evidence_traceability_pct'], '%')} |",
        f"| Unsafe confirmation events | {_display(manual['unsafe_confirmation_events'])} | {_display(opsintel['unsafe_confirmation_events'])} |",
        "",
    ]
    if report["comparison_ready"]:
        lines.extend([
            "Median time difference: "
            f"**{report['median_time_difference_pct']}%** "
            "(descriptive; positive means the assisted median was lower).",
            "Diagnosis agreement difference: "
            f"**{report['diagnosis_agreement_delta_points']} percentage points**.",
            "",
        ])
    else:
        lines.extend([
            "No condition comparison was generated because the complete "
            "assigned baseline is not available.",
            "",
        ])
    lines.extend(["## Interpretation", "", interpretation, ""])
    if report["pending_trial_ids"] or report["incomplete_trial_ids"]:
        lines.extend([
            "## Missing data",
            "",
            "Pending: " + (
                ", ".join(f"`{item}`" for item in report["pending_trial_ids"])
                or "None"
            ),
            "",
            "Incomplete: " + (
                ", ".join(f"`{item}`" for item in report["incomplete_trial_ids"])
                or "None"
            ),
            "",
        ])
    lines.extend(["## Protocol deviations", ""])
    if report["protocol_deviations"]:
        lines.extend(
            f"- `{item['trial_id']}`: {item['description']}"
            for item in report["protocol_deviations"]
        )
    else:
        lines.append("None recorded.")
    lines.extend([
        "",
        "## Recruitment",
        "",
        report["recruitment_description"],
        "",
        "## Limitations",
        "",
        *[f"- {item}" for item in report["limitations"]],
        "",
    ])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Impact-study CSV; incomplete files report pending")
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
