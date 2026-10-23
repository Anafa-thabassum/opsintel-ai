"""Score the classifier on cited, licensed public failure messages."""

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from app.investigator import _classify_evidence_details


REQUIRED = {
    "id", "project", "source_url", "license", "license_url",
    "excerpt", "expected", "labelling_note",
}


def evaluate(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or REQUIRED - set(reader.fieldnames):
            raise ValueError("Public corpus is missing required provenance fields")
        rows = list(reader)

    ids = [row["id"] for row in rows]
    if not rows or len(ids) != len(set(ids)):
        raise ValueError("Public corpus must contain unique, non-empty cases")

    results = []
    for row in rows:
        if not all(row[field].strip() for field in REQUIRED):
            raise ValueError(f"Case {row.get('id') or '<unknown>'} has an empty field")
        details = _classify_evidence_details([row["excerpt"]], 0)
        predicted = details["result"][0]
        results.append({
            **row,
            "predicted": predicted,
            "correct": predicted == row["expected"],
            "confidence": details["confidence"],
            "matched_categories": details["matched_categories"],
            "tie_break_reason": details["tie_break_reason"],
        })

    correct = sum(result["correct"] for result in results)
    return {
        "dataset": str(path),
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Project-labelled compatibility corpus; not an independent accuracy estimate.",
        "total": len(results),
        "correct": correct,
        "accuracy_pct": round(correct * 100 / len(results), 1),
        "projects": dict(sorted(Counter(row["project"] for row in rows).items())),
        "results": results,
    }


def render_markdown(report):
    lines = [
        "# Public failure-message compatibility evaluation",
        "",
        f"- Cases: **{report['total']}**",
        f"- Exact category matches: **{report['correct']}/{report['total']} ({report['accuracy_pct']:.1f}%)**",
        f"- Scope: {report['scope']}",
        "- Inputs: short framework-generated messages from Apache-2.0 repositories; source and licence URLs are recorded per case.",
        "- Limitation: labels were assigned by the OpsIntel project, not external reviewers, and the corpus is small.",
        "",
        "## Results",
        "",
        "| Case | Project | Expected | Predicted | Confidence | Result |",
        "|---|---|---|---|---|---|",
    ]
    for result in report["results"]:
        status = "PASS" if result["correct"] else "FAIL"
        lines.append(
            f"| {result['id']} | {result['project']} | {result['expected']} | "
            f"{result['predicted']} | {result['confidence']} | {status} |"
        )

    failures = [result for result in report["results"] if not result["correct"]]
    lines.extend(["", "## Published failures", ""])
    if not failures:
        lines.append("No category mismatches were observed.")
    for result in failures:
        lines.extend([
            f"### {result['id']}",
            "",
            f"- Source: [{result['project']}]({result['source_url']})",
            f"- Licence: [{result['license']}]({result['license_url']})",
            f"- Expected `{result['expected']}`; predicted `{result['predicted']}`.",
            f"- Label rationale: {result['labelling_note']}",
            "- Interpretation: the current deterministic vocabulary does not recognise this upstream phrasing; no cause was confirmed.",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default="evaluation/public_failure_corpus_v1.csv")
    parser.add_argument("--output", default="reports/public-corpus-v1.json")
    parser.add_argument("--markdown-output", default="reports/public-corpus-v1.md")
    args = parser.parse_args()
    report = evaluate(args.path)
    Path(args.output).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    Path(args.markdown_output).write_text(render_markdown(report), encoding="utf-8")
    print(f"Public corpus: {report['correct']}/{report['total']} ({report['accuracy_pct']:.1f}%)")


if __name__ == "__main__":
    main()
