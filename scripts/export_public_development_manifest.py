"""Export provenance and project labels, without redistributing GitHub issue text."""

import argparse
import csv
import json
from pathlib import Path
from urllib.parse import urlsplit

from app.public_data import list_public_incidents


ROOT = Path(__file__).resolve().parents[1]
LABELS = ROOT / "evaluation" / "public_failure_corpus_v2.csv"


def _key(url):
    parts = urlsplit(url).path.strip("/").split("/")
    if len(parts) != 4 or parts[2] != "issues":
        raise ValueError(f"Not a canonical GitHub issue URL: {url}")
    repository = f"{parts[0]}/{parts[1]}".replace("dbt-labs/dbt-core", "dbt-labs/dbt")
    return f"{repository}#{parts[3]}"


def build_manifest(records, labels):
    by_key = {item["source_key"]: item for item in records}
    output = []
    for row in labels:
        key = _key(row["source_url"])
        record = by_key.get(key)
        if record is None:
            raise ValueError(f"Public issue is not present in Exasol: {key}")
        output.append({
            "dataset_version": "public-development-evaluation-v1",
            "role": "development_only",
            "case_id": row["id"],
            "source_key": key,
            "source_url": record["source_url"],
            "source_repository": record["source_repository"],
            "source_created_at": record["source_created_at"],
            "source_updated_at": record["source_updated_at"],
            "collected_at": record["collected_at"],
            "excerpt_origin": record["excerpt_origin"],
            "source_body_sha256": record["body_sha256"],
            "repository_code_license": record["code_license"],
            "repository_license_url": record["code_license_url"],
            "issue_text_license_status": record["issue_text_license_status"],
            "source_category": row["source_category"],
            "expected_category": row["expected"],
            "label_status": "project_assigned_unreviewed",
            "label_source": "evaluation/public_failure_corpus_v2.csv",
            "label_rationale": row["labelling_rationale"],
        })
    return sorted(output, key=lambda item: item["case_id"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with LABELS.open(newline="", encoding="utf-8") as handle:
        labels = list(csv.DictReader(handle))
    records = []
    offset = 0
    while True:
        page = list_public_incidents(limit=200, offset=offset)
        records.extend(page["incidents"])
        offset += len(page["incidents"])
        if offset >= page["total"] or not page["incidents"]:
            break
    manifest = build_manifest(records, labels)
    args.output.write_text("".join(json.dumps(item, sort_keys=True) + "\n" for item in manifest), encoding="utf-8")
    print(json.dumps({"version": "public-development-evaluation-v1", "records": len(manifest),
                      "role": "development_only", "issue_text_included": False}, indent=2))


if __name__ == "__main__":
    main()
