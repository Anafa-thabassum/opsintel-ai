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
    if hashlib.sha256(frozen_dataset).hexdigest() != _sha256(path):
        raise ValueError("Holdout file differs from the frozen Git ref")
    classifier_path = repo_root / "app" / "investigator.py"
    if hashlib.sha256(frozen_classifier).hexdigest() != _sha256(classifier_path):
        raise ValueError("Classifier changed after the holdout was frozen")
    return {
        "frozen_ref": frozen_ref,
        "frozen_commit": frozen_commit,
        "dataset_frozen_sha256": hashlib.sha256(frozen_dataset).hexdigest(),
        "classifier_frozen_sha256": hashlib.sha256(frozen_classifier).hexdigest(),
    }


def _optional_int(row, name):
    value = row.get(name, "").strip()
    return int(value) if value else None


def evaluate(path, provenance="project-authored", frozen_ref=None):
    path = Path(path)
    with path.open(newline="") as source:
        cases = list(csv.DictReader(source))

    if not cases:
        raise ValueError("Holdout file contains no cases")

    independent = provenance == "independent"
    if provenance not in {"project-authored", "independent"}:
        raise ValueError("Provenance must be project-authored or independent")
    if independent and not 15 <= len(cases) <= 20:
        raise ValueError("Independent holdout must contain 15 to 20 cases")

    results = []
    seen_ids = set()
    authors = set()
    for row in cases:
        case_id = row["id"].strip()
        if not case_id or case_id in seen_ids:
            raise ValueError(f"Missing or duplicate case id: {case_id!r}")
        seen_ids.add(case_id)

        if independent:
            author_id = row.get("author_id", "").strip()
            if not author_id:
                raise ValueError(f"Case {case_id} is missing author_id")
            authors.add(author_id)

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
    if independent and not 2 <= len(authors) <= 3:
        raise ValueError("Independent holdout must have cases from 2 or 3 authors")
    freeze = (
        _validate_independent_freeze(path, repo_root, frozen_ref)
        if independent and frozen_ref
        else {}
    )
    if independent and not frozen_ref:
        raise ValueError("Independent holdout requires --frozen-ref")

    return {
        "evaluation": (
            "independent-reviewer-holdout"
            if independent
            else "frozen-synthetic-holdout-v1"
        ),
        "provenance": provenance,
        "author_ids": sorted(authors),
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
            "Unseen synthetic cases authored by external reviewers and frozen "
            "with the tested classifier; not a production accuracy estimate."
            if independent
            else "Project-authored synthetic holdout frozen before execution; "
            "not an independent or production accuracy estimate."
        ),
        **freeze,
        "results": results,
    }


def render_markdown(report):
    lines = [
        f"# {report['evaluation'].replace('-', ' ').title()}",
        "",
        f"- Provenance: **{report['provenance']}**",
        f"- Correct: **{report['correct']}/{report['total']}**",
        f"- Accuracy on this dataset: **{report['accuracy_pct']}%**",
        f"- Dataset SHA-256: `{report['dataset_sha256']}`",
        f"- Classifier SHA-256: `{report['classifier_sha256']}`",
    ]
    if report.get("frozen_ref"):
        lines.extend([
            f"- Frozen ref: `{report['frozen_ref']}`",
            f"- Frozen commit: `{report['frozen_commit']}`",
            f"- Pseudonymous case authors: {', '.join(report['author_ids'])}",
        ])
    lines.extend(["", "## Category results", "", "| Category | Correct | Total |", "|---|---:|---:|"])
    for category, values in report["category_results"].items():
        lines.append(f"| {category} | {values['correct']} | {values['total']} |")

    misses = [result for result in report["results"] if not result["correct"]]
    lines.extend(["", "## Error analysis", ""])
    if misses:
        lines.append("The evaluator recorded these misses:")
        lines.append("")
        lines.append("| Case | Expected | Predicted |")
        lines.append("|---|---|---|")
        for result in misses:
            lines.append(
                f"| {result['id']} | {result['expected']} | {result['predicted']} |"
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
    parser.add_argument("--output", help="Optional JSON report path")
    parser.add_argument("--markdown-output", help="Optional Markdown report path")
    args = parser.parse_args()
    evaluated = evaluate(args.path, args.provenance, args.frozen_ref)
    report = json.dumps(evaluated, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(report)
    if args.markdown_output:
        Path(args.markdown_output).write_text(render_markdown(evaluated))
    print(report, end="")


if __name__ == "__main__":
    main()
