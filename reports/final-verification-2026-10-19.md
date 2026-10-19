# Batch 8 final verification

Date: 19 October 2026 (Asia/Kolkata)

## Candidate state

| Item | Value |
|---|---|
| Verified revision | `13bf38821646ff0a8febaf75867a26080664d17f` |
| Branch at inspection | `main` |
| Local tracking ref | `origin/main` matched the verified revision |
| Public remote check | `git ls-remote origin refs/heads/main` returned the verified revision |
| Working tree at inspection start | Clean |
| Batch 8 changes | Uncommitted, as required |

No commit, reset, stash, amendment, database setup, database smoke test, or live
LLM request was performed.

## Checks executed

| Command | Result |
|---|---|
| `.venv/bin/python -m pytest tests/test_holdout_evaluation.py -q` | Passed: 12 tests |
| `.venv/bin/python -m pytest tests/test_impact_study.py -q` | Passed: 13 tests |
| `.venv/bin/python -m pytest tests/test_llm.py -q` | Passed: 14 tests |
| `.venv/bin/python -m pytest -q` | Passed: 132 tests |
| `.venv/bin/python -m tests.run_evaluation` | Passed: 16/16 predefined synthetic cases |
| `make holdout` | Passed: 27/27 project-authored synthetic cases; 3 correctly unresolved cases; not independent validation |
| `cd frontend && npm run lint` | Passed with no warnings |
| `cd frontend && npm run build` | Passed; main chunk 614.81 kB before gzip, above Vite's 500 kB advisory threshold |
| `make verify` | Passed: 132 tests, 16/16 evaluation, lint, and production build |
| `make submission-check` | Failed as intended: uncommitted Batch 8 changes plus five stale-deck findings |
| `git diff --check` | Passed |

The Vite chunk-size message is a non-failing performance advisory. Batch 8 does
not introduce code splitting because that would be unrelated feature work.

## Submission artifact verification

| Artifact check | Result |
|---|---|
| PPTX readability and slide count | Package parsed successfully; 11 slides |
| PDF readability and page count | Rendered and visually inspected; 11 pages |
| Existing video duration | 154.445 seconds, below the three-minute limit |
| Current video content | Blocked: recorded before the final cascade, test count, and LLM grounding changes |
| Current PPTX/PDF claims | Blocked: slides 8 and 10 still report 80/80 tests |
| Cascade wording in deck | Blocked: slide 7 says the upstream failure “explains” downstream incidents and omits the 120-minute temporal-correlation caveat |
| Clean-rehearsal wording in deck | Blocked: slide 10 lists the clean-machine rehearsal under “Defined, not completed” even though Batch 6 completed a clean-clone rehearsal with an explicitly blocked database workflow |

The corrected artifact-only command
`.venv/bin/python -m scripts.verify_submission --allow-dirty` exits with failure
until the PPTX/PDF contain the current 132/132 result and label the cascade as
temporal correlation within 120 minutes, with causation unconfirmed.

## Database and external-service boundaries

- Batch 8 did not connect to, reset, recreate, or seed Exasol.
- A historical smoke result is recorded in `reports/evaluation.md`, but the
  final revision's database-backed browser workflow was not rerun in Batch 8.
- Batch 6 verified clean dependency installation, automated checks, API process
  startup, and frontend startup at revision `2a17d4f`; live Exasol was blocked.
- Live LLM access, model-account entitlement, real-model grounding, usage, and
  cost remain unverified. Batch 7 records mocked boundary tests only.
- The external-reviewer holdout remains at 0 cases from 0 reviewers.
- The human-impact study remains at 0/40 trials from 0/4 participants.

## Repository hygiene

The tracked-file scan found no OpenAI, GitHub, AWS, or private-key signatures,
no tracked local `.env`, credential file, database, or log, and no local secret
file matching the checked names. Local `.venv`, `node_modules`, build output,
pytest caches, and presentation-validation directories are ignored. This is a
targeted signature and path scan, not a full security audit.

## Safe three-minute product workflow

Use an explicitly authorized disposable Exasol Personal database and keep the
optional LLM disabled unless a separate live request is authorized.

1. Open the dashboard and select `daily_sales_import`.
2. Show the failed run against its last success, source-backed observations,
   candidate explanations, and the unconfirmed human-verification state.
3. Show the cascade timestamps and lags for downstream failures within 120
   minutes, saying that correlation does not confirm causation.
4. Select `partner_feed` to demonstrate the unresolved path and next safe check.
5. Close with Exasol's window analytics and `CONNECT BY` role, then the verified
   test and evaluation boundaries.

## Claims that must not be made

- No measured time saving or causal human-impact result.
- No independent holdout accuracy result.
- No live LLM quality, access, or accuracy result.
- No claim that temporal cascade correlation proves causation.
- No Exasol speed advantage from the recorded comparison; DuckDB was faster in
  the local single-user workload.
- No production concurrency, authentication, live orchestrator, automatic
  recovery, or confirmed-root-cause claim.

## Remaining manual submission steps

1. Update slides 7, 8, and 10 in the PPTX, regenerate the PDF, and inspect all
   11 rendered pages.
2. Run the artifact checker until it passes after the final files are committed.
3. Against a confirmed disposable Exasol deployment, run one final database/API
   rehearsal. Do not use `make smoke` against an existing database because it
   resets the synthetic `OPSINTEL` schema.
4. Record a new video from the current narration, verify audio and duration,
   and replace the stale MP4.
5. Commit and push the Batch 8 consistency changes and refreshed artifacts,
   then perform a final clean-clone check of that exact revision.
6. Test repository, deck, and video links in a private browser window before
   submitting, and change the GitHub description so it does not imply automated
   recovery.
