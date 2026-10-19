"""Evaluate frozen holdout cases without changing the classifier."""

import argparse
import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
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
EVALUATOR_VERSION = "2.0"
SCORING_RULES_VERSION = "exact-category-v1"
CLASSIFIER_CONFIGURATION_VERSION = "deterministic-default-v1"
VALID_UNCERTAINTY = {"candidate_only", "unresolved"}
INDEPENDENT_COLUMNS = {
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


def _git_output(repo_root, *args):
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise ValueError(result.stderr.decode().strip() or "Git validation failed")
    return result.stdout


def _validate_independent_freeze(path, repo_root, frozen_ref):
    try:
        relative_path = path.resolve().relative_to(repo_root.resolve())
    except ValueError as exc:
        raise ValueError("Independent holdout must be committed inside the repository") from exc

    frozen_commit = _git_output(repo_root, "rev-parse", f"{frozen_ref}^{{commit}}").decode().strip()
    frozen_dataset = _git_output(repo_root, "show", f"{frozen_ref}:{relative_path}")
    frozen_classifier = _git_output(repo_root, "show", f"{frozen_ref}:app/investigator.py")
    frozen_evaluator = _git_output(
        repo_root,
        "show",
        f"{frozen_ref}:scripts/evaluate_holdout.py",
    )
    if hashlib.sha256(frozen_dataset).hexdigest() != _sha256(path):
        raise ValueError("Holdout file differs from the frozen Git ref")
    classifier_path = repo_root / "app" / "investigator.py"
    if hashlib.sha256(frozen_classifier).hexdigest() != _sha256(classifier_path):
        raise ValueError("Classifier changed after the holdout was frozen")
    evaluator_path = repo_root / "scripts" / "evaluate_holdout.py"
    if hashlib.sha256(frozen_evaluator).hexdigest() != _sha256(evaluator_path):
        raise ValueError("Evaluator or scoring rules changed after the holdout was frozen")
    return {
        "frozen_ref": frozen_ref,
        "frozen_commit": frozen_commit,
        "dataset_frozen_sha256": hashlib.sha256(frozen_dataset).hexdigest(),
        "classifier_frozen_sha256": hashlib.sha256(frozen_classifier).hexdigest(),
        "evaluator_frozen_sha256": hashlib.sha256(frozen_evaluator).hexdigest(),
    }


def _optional_int(row, name):
    value = row.get(name, "").strip()
    try:
        return int(value) if value else None
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer when provided") from exc


def _json_list(value, case_id, field, item_type=str):
    try:
        items = json.loads(value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Case {case_id} has invalid {field}") from exc
    if not isinstance(items, list) or not all(
        isinstance(item, item_type) for item in items
    ):
        raise ValueError(f"Case {case_id} has invalid {field}")
    return items


def _independent_evidence(row, case_id):
    evidence = _json_list(row.get("evidence_json", ""), case_id, "evidence_json", dict)
    if not evidence:
        raise ValueError(f"Case {case_id} must contain evidence")
    logs = []
    references = []
    for item in evidence:
        observation = item.get("observation")
        reference = item.get("reference")
        if not isinstance(observation, str) or not observation.strip():
            raise ValueError(f"Case {case_id} has evidence without an observation")
        if not isinstance(reference, str) or not reference.strip():
            raise ValueError(f"Case {case_id} has evidence without a reference")
        logs.append(observation.strip())
        references.append(reference.strip())
    return logs, references


def _timestamp(value):
    if value is None:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("evaluated_at must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError("evaluated_at must include a timezone")
    return parsed.isoformat()


def evaluate(
    path,
    provenance="project-authored",
    frozen_ref=None,
    evaluated_at=None,
):
    path = Path(path)
    with path.open(newline="") as source:
        reader = csv.DictReader(source)
        columns = set(reader.fieldnames or [])
        cases = list(reader)

    if not cases:
        raise ValueError("Holdout file contains no cases")

    independent = provenance == "independent"
    if provenance not in {"project-authored", "independent"}:
        raise ValueError("Provenance must be project-authored or independent")
    if independent and not 15 <= len(cases) <= 20:
        raise ValueError("Independent holdout must contain 15 to 20 cases")
    if independent:
        missing_columns = sorted(INDEPENDENT_COLUMNS - columns)
        if missing_columns:
            raise ValueError(
                "Independent holdout is missing columns: "
                + ", ".join(missing_columns)
            )

    results = []
    seen_ids = set()
    authors = set()
    dataset_versions = set()
    for row in cases:
        case_id = row.get("id", "").strip()
        if not case_id or case_id in seen_ids:
            raise ValueError(f"Missing or duplicate case id: {case_id!r}")
        seen_ids.add(case_id)

        if independent:
            author_id = row.get("author_id", "").strip()
            if not author_id:
                raise ValueError(f"Case {case_id} is missing author_id")
            if row.get("reviewer_provenance", "").strip() != "external-reviewer":
                raise ValueError(
                    f"Case {case_id} lacks external reviewer provenance"
                )
            dataset_version = row.get("dataset_version", "").strip()
            if not dataset_version:
                raise ValueError(f"Case {case_id} is missing dataset_version")
            authors.add(author_id)
            dataset_versions.add(dataset_version)
            logs, evidence_refs = _independent_evidence(row, case_id)
        else:
            logs = _json_list(row.get("logs_json", ""), case_id, "logs_json")
            if not logs or not all(log.strip() for log in logs):
                raise ValueError(f"Case {case_id} must contain non-empty log strings")
            evidence_refs = []

        expected = row.get("expected", "").strip() or None
        if expected is not None and expected not in VALID_CATEGORIES:
            raise ValueError(f"Unknown expected category: {expected}")

        expected_findings = []
        expected_uncertainty = None
        if independent and expected is not None:
            expected_findings = _json_list(
                row.get("expected_findings_json", ""),
                case_id,
                "expected_findings_json",
            )
            if not expected_findings or not all(
                finding.strip() for finding in expected_findings
            ):
                raise ValueError(f"Case {case_id} requires expected findings")
            expected_uncertainty = row.get("expected_uncertainty", "").strip()
            if expected_uncertainty not in VALID_UNCERTAINTY:
                raise ValueError(
                    f"Case {case_id} has invalid expected_uncertainty"
                )

        expected_rows = _optional_int(row, "expected_rows")
        actual_rows = _optional_int(row, "actual_rows")
        if (expected_rows is None) != (actual_rows is None):
            raise ValueError(
                f"Case {case_id} must provide both expected_rows and actual_rows"
            )
        missing_rows = _optional_int(row, "missing_rows")

        predicted, _, _ = classify_evidence(
            logs,
            missing_rows,
            expected_rows,
            actual_rows,
        )
        predicted_uncertainty = (
            "unresolved" if predicted == "unclassified" else "candidate_only"
        )
        correct = None if expected is None else predicted == expected
        result = {
            "id": case_id,
            "expected": expected,
            "predicted": predicted,
            "correct": correct,
            "inputs": {
                "logs": logs,
                "missing_rows": missing_rows,
                "expected_rows": expected_rows,
                "actual_rows": actual_rows,
            },
        }
        if independent:
            result.update({
                "outcome": (
                    "missing_label"
                    if expected is None
                    else "correct" if correct else "incorrect"
                ),
                "resolution_status": predicted_uncertainty,
                "expected_uncertainty": expected_uncertainty,
                "uncertainty_correct": (
                    None
                    if expected_uncertainty is None
                    else predicted_uncertainty == expected_uncertainty
                ),
                "expected_findings": expected_findings,
                "evidence_refs": evidence_refs,
                "evidence_traceable": len(evidence_refs) == len(logs),
                "causation_claimed": False,
            })
        results.append(result)

    if independent and len(dataset_versions) != 1:
        raise ValueError("Independent holdout must use one dataset_version")
    completed = sum(result["expected"] is not None for result in results)
    correct = sum(result["correct"] is True for result in results)
    incorrect = sum(result["correct"] is False for result in results)
    unresolved = sum(
        result["predicted"] == "unclassified" for result in results
    )
    missing_labels = len(results) - completed
    category_results = {}
    for result in results:
        if result["expected"] is None:
            continue
        category = category_results.setdefault(
            result["expected"], {"correct": 0, "total": 0}
        )
        category["correct"] += int(result["correct"])
        category["total"] += 1

    repo_root = Path(__file__).resolve().parents[1]
    if independent and not 2 <= len(authors) <= 3:
        raise ValueError("Independent holdout must have cases from 2 or 3 authors")
    freeze = (
        _validate_independent_freeze(path, repo_root, frozen_ref)
        if independent and frozen_ref
        else {}
    )
    if independent and not frozen_ref:
        raise ValueError("Independent holdout requires --frozen-ref")

    validation_status = (
        "complete"
        if independent and missing_labels == 0
        else "pending" if independent else "not-independent"
    )
    traceable_cases = (
        sum(result["evidence_traceable"] is True for result in results)
        if independent else None
    )

    return {
        "evaluation": (
            "independent-reviewer-holdout"
            if independent
            else "frozen-synthetic-holdout-v1"
        ),
        "provenance": provenance,
        "author_ids": sorted(authors),
        "independent_validation_status": validation_status,
        "dataset_version": (
            next(iter(dataset_versions))
            if independent else "project-authored-v1"
        ),
        "dataset_file": path.name,
        "dataset_sha256": _sha256(path),
        "evaluated_at": _timestamp(evaluated_at),
        "evaluator_version": EVALUATOR_VERSION,
        "classifier_configuration_version": CLASSIFIER_CONFIGURATION_VERSION,
        "scoring_rules_version": SCORING_RULES_VERSION,
        "scoring_rules": (
            "Exact category match receives credit; partial category matches "
            "receive no credit. Unclassified predictions remain unresolved. "
            "Missing labels are reported and excluded from accuracy."
        ),
        "classifier_file": "app/investigator.py",
        "classifier_sha256": _sha256(repo_root / "app" / "investigator.py"),
        "classifier_commit": _git_commit(repo_root),
        "correct": correct,
        "total": len(results),
        "total_cases": len(results),
        "completed_cases": completed,
        "correct_findings": correct,
        "incorrect_findings": incorrect,
        "unresolved_cases": unresolved,
        "missing_labels": missing_labels,
        "accuracy_pct": (
            round(correct * 100 / completed, 1) if completed else None
        ),
        "traceable_cases": traceable_cases,
        "causation_safe_cases": sum(
            not result.get("causation_claimed", False) for result in results
        ),
        "category_results": dict(sorted(category_results.items())),
        "scope": (
            "Unseen synthetic cases authored by external reviewers and frozen "
            "with the tested classifier and evaluator; not a production "
            "accuracy estimate."
            if independent
            else "Project-authored synthetic holdout frozen before execution; "
            "not an independent or production accuracy estimate."
        ),
        **freeze,
        "results": results,
    }


def render_markdown(report):
    accuracy = (
        f"{report['accuracy_pct']}%"
        if report["accuracy_pct"] is not None
        else "not available"
    )
    lines = [
        f"# {report['evaluation'].replace('-', ' ').title()}",
        "",
        f"- Provenance: **{report['provenance']}**",
        f"- Independent validation status: **{report['independent_validation_status']}**",
        f"- Dataset version: `{report['dataset_version']}`",
        f"- Evaluated at: `{report['evaluated_at']}`",
        f"- Evaluator version: `{report['evaluator_version']}`",
        "- Classifier configuration: "
        f"`{report['classifier_configuration_version']}`",
        f"- Scoring rules: `{report['scoring_rules_version']}`",
        f"- Total cases: **{report['total_cases']}**",
        f"- Completed cases: **{report['completed_cases']}**",
        f"- Correct findings: **{report['correct_findings']}**",
        f"- Incorrect findings: **{report['incorrect_findings']}**",
        f"- Unresolved predictions: **{report['unresolved_cases']}**",
        f"- Missing labels: **{report['missing_labels']}**",
        f"- Accuracy on completed cases: **{accuracy}**",
        f"- Dataset SHA-256: `{report['dataset_sha256']}`",
        f"- Classifier SHA-256: `{report['classifier_sha256']}`",
    ]
    if report["traceable_cases"] is not None:
        lines.append(
            f"- Cases with complete evidence references: "
            f"**{report['traceable_cases']}/{report['total_cases']}**"
        )
    lines.append(
        f"- Outputs that avoided a causation claim: "
        f"**{report['causation_safe_cases']}/{report['total_cases']}**"
    )
    if report.get("frozen_ref"):
        lines.extend([
            f"- Frozen ref: `{report['frozen_ref']}`",
            f"- Frozen commit: `{report['frozen_commit']}`",
            f"- Pseudonymous case authors: {', '.join(report['author_ids'])}",
            f"- Frozen evaluator SHA-256: `{report['evaluator_frozen_sha256']}`",
        ])
    lines.extend([
        "",
        "## Scoring rules",
        "",
        report["scoring_rules"],
        "Expected findings and uncertainty are reported separately and do not "
        "create partial category credit.",
    ])
    lines.extend(["", "## Category results", "", "| Category | Correct | Total |", "|---|---:|---:|"])
    for category, values in report["category_results"].items():
        lines.append(f"| {category} | {values['correct']} | {values['total']} |")

    misses = [
        result for result in report["results"]
        if result["correct"] is False
    ]
    lines.extend(["", "## Error analysis", ""])
    if misses:
        lines.append("The evaluator recorded these misses:")
        lines.append("")
        lines.append("| Case | Expected | Predicted | Evidence reviewed | Next fix to test |")
        lines.append("|---|---|---|---|---|")
        for result in misses:
            inputs = result["inputs"]
            evidence = "; ".join(inputs["logs"])
            if inputs["expected_rows"] is not None:
                evidence += (
                    f"; rows {inputs['actual_rows']}/{inputs['expected_rows']}"
                    f"; missing {inputs['missing_rows']}"
                )
            safe_evidence = evidence.replace("|", "\\|")
            lines.append(
                f"| {result['id']} | {result['expected']} | {result['predicted']} "
                f"| {safe_evidence} "
                "| Add the smallest rule or abstention test that separates the "
                "expected category without changing this frozen result. |"
            )
        lines.extend([
            "",
            "Review the cited cases before changing the rules. Preserve the frozen "
            "result and publish any later classifier version as a separate evaluation.",
        ])
    else:
        lines.append(
            "No misses occurred in this small dataset. This does not establish "
            "production accuracy or performance on other log formats."
        )

    missing = [
        result["id"] for result in report["results"]
        if result["expected"] is None
    ]
    lines.extend(["", "## Missing labels", ""])
    lines.append(
        ", ".join(f"`{case_id}`" for case_id in missing)
        if missing else "No ground-truth labels are missing."
    )

    unresolved = [
        result["id"] for result in report["results"]
        if result["predicted"] == "unclassified"
    ]
    lines.extend(["", "## Unresolved predictions", ""])
    lines.append(
        ", ".join(f"`{case_id}`" for case_id in unresolved)
        if unresolved else "No case produced an unresolved prediction."
    )
    lines.extend(["", "## Scope", "", report["scope"], ""])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Frozen holdout CSV")
    parser.add_argument(
        "--provenance",
        choices=("project-authored", "independent"),
        default="project-authored",
    )
    parser.add_argument("--frozen-ref", help="Git tag or commit containing the frozen data and classifier")
    parser.add_argument(
        "--evaluated-at",
        help="Optional ISO-8601 timestamp for byte-reproducible reports",
    )
    parser.add_argument("--output", help="Optional JSON report path")
    parser.add_argument("--markdown-output", help="Optional Markdown report path")
    args = parser.parse_args()
    evaluated = evaluate(
        args.path,
        args.provenance,
        args.frozen_ref,
        args.evaluated_at,
    )
    report = json.dumps(evaluated, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(report)
    if args.markdown_output:
        Path(args.markdown_output).write_text(render_markdown(evaluated))
    print(report, end="")


if __name__ == "__main__":
    main()
