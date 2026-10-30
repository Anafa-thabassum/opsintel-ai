# New independent validation — status: development-only

No independent reviewers participated in this task. Therefore this artifact is
**not an independent validation set** and the report makes no independent
accuracy claim. The newly versioned manifest is explicitly development-only;
its ten project-assigned labels were copied from the already existing public
corpus V2 mappings. They must not be exposed as hidden evaluation labels or
used to claim generalization.

## Dataset

- Manifest: `evaluation/public_development_evaluation_v1.jsonl`
- Cases: 10; all in one development split; no train/evaluation split.
- Sources: nine Apache Airflow issues and one dbt issue.
- Collected: GitHub API metadata was fetched into local Exasol on 2026-10-30.
- Included provenance: canonical URL, repository, issue ID, source timestamps,
  collection timestamp, excerpt line reference, source-body SHA-256, repository
  code licence URL, issue-text licence status, project label, label source and
  rationale.
- Excerpt/title text is not copied into this JSONL manifest. Re-fetch through
  `make public-ingest`; short screened excerpts remain in the local Exasol
  cache.
- Label status for every row: `project_assigned_unreviewed`.
- SHA-256: `912181f09c2f8a4dfd4269e9b0e00f0a14c1c8bcd956a73bfb359633f3b77fa1`.
- Source registry: `evaluation/public_source_registry_v1.json`.

## Current descriptive result

The separate public-data report records 7/10 exact category matches, six
unresolved predictions, and 10/10 source-reference records. These are
compatibility results against project-assigned mappings, not independent
reviewer labels. The three project `dependency_failure` mappings involving
`ModuleNotFoundError` remain questionable: a missing Python module alone does
not establish that an upstream pipeline dependency failed. No labels or
classifier rules were changed to improve this score.

## Integrity and limits

The frozen 19-case reviewer holdout, historical evaluator and report hashes
remain unchanged. This ten-case manifest has no duplicate split members, but
it reuses cases and project labels already present in the public development
corpus, so it is not a new independent sample. Ten cases do not meet the
30-case target. GitHub issue discussions remain user-generated content with no
separately established redistribution licence; full issue bodies are not
included.

To create a real independent set, an external reviewer must select or author
at least 30 cases, record evidence and label rationale without seeing OpsIntel
predictions, then adjudicate disagreements before a dated, source-grouped split
is frozen. Until then, use this manifest for development checks only. Do not
use it to tune the frozen holdout or report independent accuracy.
