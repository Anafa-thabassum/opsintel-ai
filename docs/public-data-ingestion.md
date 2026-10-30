# Public issue ingestion

Public Data Investigation is a separate Exasol-backed mode. It does not import
GitHub issues into confirmed incident memory or synthetic pipeline telemetry.

## Run

Start an authorized Exasol Personal deployment with an initialized `OPSINTEL`
schema. Apply additive migrations, then fetch the source registry:

```bash
python -m scripts.migrate_database --apply
python -m scripts.ingest_public_issues
python -m scripts.evaluate_public_data --json-output reports/public-data-evaluation.json --markdown-output reports/public-data-evaluation.md
```

Open `http://127.0.0.1:5173/#/public` after starting the API and frontend.
`GITHUB_TOKEN` is optional for higher read-only GitHub API rate limits. Do not
put it in the frontend or commit it. The CLI may also ingest one source with
`--repository apache/airflow` or `--repository dbt-labs/dbt`.

The registry is `evaluation/public_source_registry_v1.json`. It pins the exact
issue IDs and source repositories. Each run uses GitHub's official issue API,
checks issue identity, selects one diagnostic line or the issue title, screens
common secrets, email addresses, IPs and absolute paths, stores timestamps and
a SHA-256 of the original body, and applies the deterministic classifier to
the screened excerpt. It retries transient failures at most twice and reports
per-issue failures. Rows are keyed by repository and issue number; repeating
the command leaves unchanged records untouched. Cached records remain
queryable without GitHub access after ingestion.

Unauthenticated GitHub API access can exhaust its hourly limit. The CLI then
reports the reset time and suggests `GITHUB_TOKEN`; already cached records
stay available. A failed refresh exits nonzero so automation cannot silently
report complete ingestion.

To remove one locally cached record, use
`python -m scripts.ingest_public_issues --remove 'apache/airflow#46378'`.
Removal is physical deletion from the local public table. It does not alter
the original GitHub issue or the versioned source registry.

The source list currently has nine Airflow issues and one dbt issue. The dbt
issue's historical scorecard URL used `dbt-labs/dbt-core`; its canonical API
and issue URL now use `dbt-labs/dbt`. The public mode records the canonical
URL, while the frozen scorecard remains unchanged.

## Limits

The short excerpt can omit context, resolution and contradictory evidence.
Issue titles/bodies are user-generated content; the repository's Apache-2.0
code licence does not itself license issue text for redistribution. The local
cache retains only short, screened excerpts, and the UI links to each original.
The screening is heuristic, so inspect additions before sharing a database
dump. The API does not depend on GitHub during normal operation.

LogHub was inspected but excluded: its repository licence restricts use to
research/academic purposes, and raw logs may require further privacy review.
Do not label unlabeled LogHub records or ingest them without that review.
