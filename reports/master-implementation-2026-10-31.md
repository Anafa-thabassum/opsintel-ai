# OpsIntel AI implementation review — 2026-10-31

## Executive summary

OpsIntel now has an additive Exasol-backed verified-incident memory, a deterministic incident fingerprint, role-gated investigator and reviewer actions, candidate-only historical retrieval, chronological evaluation tooling, and a React memory workflow. The classifier remains deterministic and abstains when its supported taxonomy lacks evidence. Existing investigation and Exasol analytical paths remain available. No automatic repair or automated root-cause confirmation was added.

The product is a working prototype, not an independently validated diagnostic system. No real human-confirmed incident was retained in memory, no new independent holdout was scored, and no participant study or memory benchmark was measured. A rollback-only transaction rehearsal verified the new SQL path against local Exasol Personal; it is not evidence of causal accuracy or human workflow effectiveness.

## Priority status

| Priority | Status | Implemented | Verification and limit |
|---|---|---|---|
| 1. Classifier | Partial | Kept evidence normalization, structured signals, multi-symptom and scoped-conflict semantics; added general exception/import timeout recognition and regressions | 182 Python tests pass; synthetic 16/16; project-labelled public scorecard 7/10. No fresh independent validation. |
| 2. Verified Memory | Partial | Five additive Exasol tables, migration ledger, fingerprinting, reviewer workflow, correction/revocation, active-only candidate retrieval, audit | Local Exasol migration and rollback-only transaction path passed. No retained human-confirmed record or empirical review-policy validation. |
| 3. Evaluation and impact | Partial | Prequential evaluation harness and protocols/reports with explicit missing results | No suitable adjudicated chronological cause dataset, repeated memory benchmark, or participant observations. No learning-curve numbers or time-savings claim. |
| 4. Dashboard and UX | Partial | Responsive verified-memory panel, evidence packet, similar candidates, reviewer checklist, history and operational counts; existing investigation views retained | Vite build, Oxlint, and narrow/mobile browser QA passed. No automated frontend interaction suite or judge study. |
| 5. Docs and demo | Partial | Architecture, APIs, Exasol SQL division, governance, deployment, demo script, and reproducibility guides | Historical deck/video remain dated drafts and do not show verified memory; a new recording is required. |
| 6. Open source and CI | Partial | Submission verifier corrected to distinguish current tests from historical asset claims; reset guard, auth documentation, contribution and security guidance | Local checks pass. Hosted GitHub Actions on its Python 3.12/Node 20 runners has not run for these uncommitted changes. |

## Architecture and actual Exasol use

`PIPELINE_RUNS`, logs, row counts and dependencies in Exasol feed the existing analytical investigation. `OPSINTEL.PIPELINE_HEALTH_FEATURES` uses window functions for previous status, rolling row baselines, completeness and failure rates; the dependency cascade query uses `CONNECT BY`. The deterministic classifier produces observed symptom categories and an explicit unresolved state. The new `app/fingerprint.py` normalizes volatile log values, retains diagnostic terms, extracts word pairs and structured features, and versions the algorithm. It does not assign causal certainty.

An investigator submits a specific cause hypothesis with distinct source-backed symptom and causal evidence. A separate configured reviewer attests the category-specific and common checks. A passing review writes a confirmed incident, feature rows and audit entry in one Exasol transaction. Rejection or request for evidence stays unconfirmed. Corrections retain a revision and audit record; revocation removes the record from future candidate selection. The database stores confirmations, submissions, features, candidate/rejected matches and audit history in five new tables. `SCHEMA_MIGRATIONS` records the additive migration hash.

Exasol filters active, non-self confirmed records and stores the resulting match decisions. The application computes bounded token-pair Jaccard and structured-feature comparison because token sets are JSON and the present candidate scan is limited to 500 recent records. This can miss older relevant incidents. A match is always a candidate requiring new engineer verification; similarity is a retrieval score, not a probability. New memory calls require configured bearer grants. No grant configuration returns 503 rather than exposing mutable memory anonymously. Existing API fields remain present.

The local Exasol Personal schema already contained sample telemetry. The migration applied without resetting it. A subsequent no-op migration check succeeded. A transaction-only exercise traversed submit, reviewer-decision SQL, candidate retrieval, rejection, revocation and audit, then rolled back all writes. A fresh read found zero rows in all five memory data tables. A single-log submission without separate causal evidence was rejected. This establishes SQL compatibility for the exercised path; it does not establish a completed real confirmation-to-retrieval demonstration.

## Evaluation and integrity

| Evidence | Result | Interpretation |
|---|---:|---|
| Original independent reviewer holdout | Historical baseline 4/19 (21.1%) | Frozen historical result, not rerun or tuned here. |
| Previously reported same-reviewer comparison | Historical 15/19 | Reused the same reviewer cases; not fresh independent validation and not attributed to classifier v2.1. |
| Predefined synthetic challenge | 16/16 | Local compatibility check, not production accuracy. |
| Public issue-linked compatibility scorecard | 7/10 | Project-labelled development/compatibility set. Three `ModuleNotFoundError` misses remain unresolved because missing Python modules do not establish a failed required upstream pipeline dependency. Issue-body licensing is not separately confirmed. |
| Public development corpus V2 | 2/2 contract cases in the Python suite | Approved for development only, with provisional cross-domain and label limitations; not an independent estimate. |
| Memory top-1, top-3, false-match, abstention, coverage, selective accuracy, learning curve | Not measured | No independently adjudicated chronological cause/query set exists. The evaluation script provides the leakage-checked calculation once one is available. |
| Human time, correctness and evidence usefulness | Not measured | No participant observations; no time-savings claim. |

Protected SHA-256 values after implementation match the recorded values:

| Protected asset | SHA-256 |
|---|---|
| `evaluation/independent_holdout_v1.csv` | `64d766d4782ee94223796e91d79c35fb359d3dcd9de414b1b8ebed41afacf71b` |
| `evaluation/public_development_corpus_v2.jsonl` | `2b16264d2954e57f9202dc3d9fa2e00e04d466598748caeb31e158381c331a5e` |
| `scripts/evaluate_holdout.py` | `c07b1f2ddcc3b5e1f11447bf8f7aa98501c2f99c5d8f3657106945254d9feb75` |
| `reports/independent-holdout-v1.json` | `79b54ba0825313089ed44b13d9ae87c7f3edcbbc5186658ed6a240fc9001235a` |
| `reports/independent-holdout-v1.md` | `6a9e58bc1322e591eb8bbe43e630c57bebd762c3f45c2bdc35b70de5598824c2` |

The frozen evaluation machinery, historical reports, labels and submission media were not edited. The public scorecard was evaluated in memory without regenerating its historical report. The evaluator's version-lock bypass was not persisted.

## Verification performed

| Command or check | Result |
|---|---|
| `.venv/bin/python -m pytest -q` | 182 passed, 0 failed, 0 skipped. Includes classifier, memory, API, migration, setup guard and evaluation-harness regressions. |
| `.venv/bin/python -m tests.run_evaluation` | 16/16 predefined synthetic cases pass. |
| `scripts.evaluate_public_corpus.evaluate('evaluation/public_failure_corpus_v2.csv')` | 7/10, read-only. |
| `.venv/bin/python -m scripts.verify_submission --allow-dirty` | `failures: []`, current test count 182; historical deck/video/test figures remain dated. `--allow-dirty` is required because the user requested no commit. |
| `npm run lint` and `npm run build` in `frontend` | Both pass. Vite reports a non-failing 632.77 kB main-chunk advisory. |
| `git diff --check` | Passes. |
| Local Exasol Personal migration plus rollback-only memory SQL path | Passes; no retained confirmation. Temporary backend, frontend and Exasol services stopped after QA. |

Local versions were Python 3.14.0 and Node 26.11.1. GitHub Actions specifies Python 3.12 and Node 20; its exact environment has not been verified with these uncommitted changes. The local `.venv` and `frontend/node_modules` supplied dependencies. CI itself is not claimed green.

## Main file changes

- `app/fingerprint.py`, `app/memory.py`, `sql/migrations/001_verified_incident_memory.sql` and `scripts/migrate_database.py`: fingerprint, memory lifecycle, additive schema and versioned migration.
- `app/main.py` and `app/db.py`: memory endpoints, explicit role grants, bounded database timeouts, request IDs and safe error responses.
- `app/classification.py`: small general timeout recognition update, with human confirmation still outside the classifier.
- `frontend/src/VerifiedMemory.jsx`, `frontend/src/App.jsx` and `frontend/src/App.css`: memory workflow and responsive integration into the existing interface.
- `scripts/evaluate_memory.py`: chronological, self-match-free evaluation harness; `scripts/setup_database.py`: reset protection when verified memory exists.
- `tests/test_verified_memory.py`, `tests/test_memory_evaluation.py` and existing test modules: regression, boundary and migration checks.
- `README.md`, `.env.example`, `Makefile`, `CONTRIBUTING.md`, `SECURITY.md`, architecture/API/governance/demo documents, and three pending-evidence reports: setup and limitations.
- `scripts/verify_submission.py`: current test-count check while keeping historical 159-test deck/report/narration assertions intact.

No files were deleted. The working tree contains these uncommitted changes; no commit or push was made.

## Remaining risks and decisions

1. The reviewer policy and seven class-specific criteria are approved design gates, not empirically validated causal-verification rules. A reviewer must inspect external HTTPS source material; the API stores the URI and excerpt but does not independently fetch or certify it.
2. No real, independently reviewed cause set is available to test match quality, false matches, the learning curve or human impact. The two-case public development corpus cannot fill that role.
3. Candidate retrieval scans at most 500 recent active records. This is simple and explainable but can omit older relevant confirmations and has no measured large-history latency.
4. The current React screen has no automated interaction tests. Browser QA covered a narrow viewport and empty-memory state, not a retained human confirmation.
5. The historical deck and 2:34 video predate memory. Their preserved claims are dated; a new evidence-grounded demonstration is needed before submission.
6. These changes have not been run by hosted CI because the current task explicitly prohibited committing or pushing them.

## Conservative hackathon readiness assessment

| Criterion | Evidence-based estimate | Reason |
|---|---:|---|
| Innovation and problem impact (25) | 17 | Distinct verified-memory workflow, but no measured engineer benefit. |
| Effective use of Exasol Personal (25) | 19 | Existing analytical SQL plus additive durable memory validated locally; no scaled memory benchmark. |
| Technical excellence (20) | 14 | Passing local tests and explicit safety gates; no hosted run or real-cause validation. |
| Solution design and UX (15) | 10 | Integrated responsive workflow; incomplete end-to-end participant demonstration. |
| Documentation and reproducibility (10) | 8 | Commands and limits documented; dated submission media. |
| Open-source quality (5) | 4 | MIT and contribution/security guidance; changes remain uncommitted. |
| **Total (100)** | **72** | A provisional self-assessment, not an organizer score. |

## Developer actions that require participation

1. Supply two distinct authorized test grants and source-backed symptom and causal records for a disposable Exasol demonstration; have an authorized reviewer verify the evidence. Do not create a confirmation from the sample logs alone.
2. Arrange independent adjudicators for a new chronological cause/query dataset and participants for the approved impact study. Keep the frozen 19-case asset untouched.
3. Review the uncommitted changes and, when satisfied, approve a commit/push so the hosted CI matrix can run. Re-record the demo and update the submission deck using only verified outcomes.
