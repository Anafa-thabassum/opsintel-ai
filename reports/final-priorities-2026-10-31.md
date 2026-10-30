# Final priorities implementation status — 2026-10-31

This report records the current local working tree. The repository remains on
`main`; these changes are uncommitted and have not been pushed. A previous
successful hosted GitHub Actions run belongs to commit `1a1c936`, before these
working-tree changes, so it is not CI evidence for this version.

## Status by priority

| Priority | Status | Implemented and verified | Remaining limit |
|---|---|---|---|
| 1. Verified Incident Memory | Partial | Added a configurable similarity cutoff (`OPSINTEL_MEMORY_MIN_SIMILARITY`), historical evidence/reviewer details to retrieved candidates, reviewer-only queue visibility, investigator-owned submission history, conflict visibility and approval blocking while conflicts remain. Added API, role, evidence and configuration tests. | The full real-world submit → separate reviewer → Exasol confirmation → restart → retrieval → engineer decision path was not performed in this change. A retained, source-backed human confirmation and live failure/correction/revocation rehearsal still require an authorized Exasol instance and reviewer. Similarity is a candidate score, not correctness probability. The default 0.42 threshold is configurable but not calibrated by this development sample. |
| 2. Public data | Partial | The existing official GitHub API ingestion path uses Airflow/dbt issues and cached them in Exasol; the UI supports source/category search and evidence inspection. Added a reproducible metadata-only manifest export with issue URLs, timestamps, hashes, licence status, label provenance and rationale. | The source is nine Airflow issues and one dbt issue; one unauthenticated refresh hit GitHub's rate limit. Issue text has no separately established redistribution licence. No LogHub logs were redistributed or labelled. The current manifest is derived from the existing cache, not a new collection. |
| 3. Independent validation | Partial | Added `evaluation/public_development_evaluation_v1.jsonl` and `reports/new-independent-validation.md` with provenance and limitations. Manifest SHA-256: `912181f09c2f8a4dfd4269e9b0e00f0a14c1c8bcd956a73bfb359633f3b77fa1`. | There are 10 records, project-assigned labels and no outside adjudicators. It is development-only, reuses existing cases, misses the 30-case target, and is not independent validation. No fresh independent accuracy claim is made. |
| 4. Memory learning curve and benchmark | Partial | Improved the prequential evaluator with a configurable threshold, source-reference validation, confusion matrix, per-category precision/recall, Wilson intervals, false-match/coverage values by memory size, and sample counts. Added an SVG plotter that uses evaluator output and draws no invented points when results are absent. | No new valid cause-confirmed chronological event set was available, so no measured learning curve or new Exasol benchmark is claimed. Existing memory matching benchmark and learning-curve reports remain explicit about unavailable measurements. |
| 5. Enterprise UI | Partial | Added reviewer/investigator role-aware submission views and conflict-aware review controls, displayed supporting historical evidence and reviewer attribution, added persisted dark/light theme controls, and built a selectable dependency cascade graph. | No complete desktop/mobile walkthrough of every route, automated frontend interaction suite, responsive acceptance matrix, or dedicated Analytics and Incident History workspaces was completed. Do not treat unvisited controls as verified. |

## Public data record

The source collection contains ten official GitHub issue records: nine from
`apache/airflow` and one from `dbt-labs/dbt`. The existing ingestion run loaded
them into the separate Exasol public incident table. Their short screened
excerpts remain in the local Exasol cache; the new versioned JSONL artifact
contains metadata only. Each manifest row retains canonical URL and issue ID,
source and retrieval timestamps, a SHA-256 of the source body, excerpt origin,
repository-code licence URL, issue-text licence status, label source, project
label, and rationale. Repository code licences do not independently establish
rights to redistribute user-authored issue text. No credentials or full issue
bodies are included in the artifact.

The reported 7/10 category compatibility result, six unresolved predictions,
and 10/10 source-reference records derive from project labels. Three
`ModuleNotFoundError` examples mapped to `dependency_failure` remain
questionable because a missing Python package does not alone establish an
upstream pipeline dependency failure. This report does not treat those labels
as ground truth or tune the classifier against them.

## Verification

| Check | Result |
|---|---|
| `.venv/bin/python -m pytest -q` | 197 passed, 0 failed, 0 skipped |
| `.venv/bin/python -m tests.run_evaluation` | 16/16 predefined synthetic challenge cases; not production accuracy |
| `npm run lint` | Passed |
| `npm run build` | Passed; Vite reports a non-failing 650.06 kB main-chunk size advisory |
| `.venv/bin/python -m scripts.verify_submission --allow-dirty` | Passed; 197 tests recorded and no submission-artifact failures |
| Frozen-holdout hashes | Unchanged at initial and final inspection; values listed below |
| Hosted CI on current tree | Not run; current changes are uncommitted |
| Public-data UI | Reloaded local app and inspected populated public workspace: 10 records, provenance and evidence links visible; not a complete all-route or mobile QA pass |
| Live Exasol memory workflow | Existing ten-record public ingestion is available locally; the full reviewer confirmation/restart/retrieval journey was not verified |

Protected hashes:

| Asset | SHA-256 |
|---|---|
| `evaluation/independent_holdout_v1.csv` | `64d766d4782ee94223796e91d79c35fb359d3dcd9de414b1b8ebed41afacf71b` |
| `evaluation/public_development_corpus_v2.jsonl` | `2b16264d2954e57f9202dc3d9fa2e00e04d466598748caeb31e158381c331a5e` |
| `scripts/evaluate_holdout.py` | `c07b1f2ddcc3b5e1f11447bf8f7aa98501c2f99c5d8f3657106945254d9feb75` |
| `reports/independent-holdout-v1.json` | `79b54ba0825313089ed44b13d9ae87c7f3edcbbc5186658ed6a240fc9001235a` |
| `reports/independent-holdout-v1.md` | `6a9e58bc1322e591eb8bbe43e630c57bebd762c3f45c2bdc35b70de5598824c2` |

The original independent result remains 4/19 (21.1%); the previously reported
15/19 comparison is not fresh independent validation. Neither result was
rerun or relabelled here. The historical report and frozen assets remain
unchanged.

## Main files changed

- Memory/API: `app/memory.py`, `app/main.py`, `.env.example`.
- UI: `frontend/src/VerifiedMemory.jsx`, `frontend/src/App.jsx`,
  `frontend/src/App.css`, `frontend/src/PublicData.jsx`,
  `frontend/src/PublicData.css`.
- Evaluation: `scripts/evaluate_memory.py`,
  `scripts/export_public_development_manifest.py`,
  `scripts/plot_learning_curve.py`, and two test modules.
- Data and documentation: `evaluation/public_development_evaluation_v1.jsonl`,
  `reports/new-independent-validation.md`,
  `reports/learning-curve-evaluation.md`, README and evaluation/public-data
  methodology docs.

## Required human actions

1. Provide an authorized disposable Exasol instance and separate investigator
   and reviewer identities to verify the real confirmation/retrieval lifecycle.
2. Recruit independent reviewers to create and adjudicate a new source-backed
   evaluation set before making independent-validation claims.
3. Review the uncommitted diff. After approval, run hosted CI on a commit; this
   task did not commit or push anything.
