"""Measure the cached public-issue mode against its stated label provenance."""

import argparse
import json
from pathlib import Path

from app.public_data import evaluate_public_records


def render(report):
    lines = ["# Public incident investigation evaluation", "",
             f"- Collected public issues in Exasol: **{report['total_collected']}**",
             f"- Project-labelled: **{report['project_labelled']}**; unlabelled: **{report['unlabelled']}**",
             f"- Exact category matches: **{report['exact_category_matches']}/{report['project_labelled']}**",
             f"- Unresolved rate: **{report['unresolved_rate']}**",
             f"- Source-reference coverage: **{report['evidence_coverage']}**; requires a canonical issue URL, body hash, excerpt origin and signal references where present.",
             "- False-match rate: **not measured**; no verified public causes are available.",
             f"- Label provenance: {report['label_provenance']}.",
             f"- Limitation: {report['limitations']}",
             "- Project `dependency_failure` mappings for `ModuleNotFoundError` need independent review: a missing Python module does not alone prove an upstream pipeline dependency failure.",
             "- GitHub issue text is user-generated content; the repository code licence does not establish a separate redistribution licence for it.",
             "", "## Every result", "",
             "| Source | Project label | Classifier | Match |", "|---|---|---|---|"]
    for item in report["results"]:
        lines.append(f"| [{item['source_key']}]({item['source_url']}) | {item['expected'] or 'unlabelled'} | {item['predicted']} | {'yes' if item['correct'] else 'no' if item['correct'] is False else 'not scored'} |")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args()
    report = evaluate_public_records()
    if args.json_output:
        args.json_output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.markdown_output:
        args.markdown_output.write_text(render(report), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "results"}, indent=2))


if __name__ == "__main__":
    main()
