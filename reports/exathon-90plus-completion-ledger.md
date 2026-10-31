# ExaThon implementation completion ledger

**Updated:** 2026-10-31  
**Repository:** OpsIntel AI, local `main` working tree  
**Changes:** uncommitted; no commit or push performed.

This ledger tracks the 33 requested implementation work items against the
repository and the verification performed in this run. `COMPLETE` means the
code or artifact exists and its stated local check passed. `PARTIAL` means an
implementation exists but the requested proof or full scope is missing.
`BLOCKED` means a required external service, data source, or human input was
not available. A code path is not described as live Exasol behavior unless it
was exercised against Exasol.

## 33-item checklist

| # | Work item | Status | Evidence / remaining work |
|---:|---|---|---|
| 1 | Preserve existing repository work and protected evaluation assets | COMPLETE | Pre-existing uncommitted changes were preserved. Protected evaluation assets were not edited. |
| 2 | Deterministic classifier and evidence normalization | COMPLETE | Existing classifier implementation and regressions retained; `make verify` classifier challenge passes. |
| 3 | Public, provenance-tracked failure examples | PARTIAL | Existing ten-source V2 remains unchanged; new independent public source candidates and label/license caveats are listed separately in `reports/public-independent-incident-candidates-v1.md`. No candidate was added to a dataset. |
| 4 | Exasol pipeline analytics | COMPLETE | Existing SQL uses window analytics and dependency traversal; unchanged in this work. |
| 5 | Additive verified-memory schema | COMPLETE | `make memory-check` connected after safe `exasol start --wait-timeout-minutes 3`; no pending migrations, additive memory/public migrations present and usable. |
| 6 | Versioned log fingerprints and structured features | COMPLETE | `app/fingerprint.py` normalizes volatile values and versions fingerprints. |
| 7 | Match current runs to confirmed incidents | COMPLETE | Live retrieval after app restart found the source-derived query at 0.5855 against default threshold 0.42 and returned cited historical evidence. Temporary confirmation was subsequently revoked and match marked stale. |
| 8 | Traceable candidate evidence and explanations | COMPLETE | Candidate response and UI expose matching/differing features and current/historical evidence references. |
| 9 | Candidate status distinct from root-cause confirmation | COMPLETE | Retrieval is labeled as candidate-only; similarity is explicitly not a probability. |
| 10 | Investigator-submitted cause hypothesis | COMPLETE | Existing API requires a specific hypothesis and source-backed evidence. |
| 11 | Authorized reviewer confirmation and no self-approval | PARTIAL | Live role/state workflow and distinct actors verified with temporary test tokens; no real authorized human adjudication was performed. |
| 12 | Cause-specific verification criteria and contradiction handling | PARTIAL | Versioned criteria and unresolved-conflict gates exist; policies are not empirically validated. |
| 13 | Atomic, race-safe reviewer decision | COMPLETE | Against live Exasol, two simultaneous reviewers produced exactly one HTTP 200 and one HTTP 409; SQL showed one confirmation and one confirmation audit, with no duplicate transition. |
| 14 | Audit, correction, revocation, and restart persistence | PARTIAL | Live confirmation persisted across app restart; audited revoke produced one revocation event and stale match. Correction workflow was not exercised; test confirmation is now revoked. |
| 15 | One-click synthetic demo entry | COMPLETE | Home-page action enters the temporary browser demo session without the email form. |
| 16 | Verified-memory reviewer and investigator UI | PARTIAL | Existing role-aware UI remains; a full rehearsal checklist is prepared in `docs/verified-incident-memory-browser-rehearsal.md`, but no real-human browser rehearsal occurred. |
| 17 | Current and historical evidence comparison | COMPLETE | Similar-memory card displays the current investigation evidence separately from historical evidence. |
| 18 | Chronological leave-one-out / prequential evaluation | PARTIAL | Leakage-checked chronological evaluation harness exists; no adjudicated confirmation/query event stream is available. |
| 19 | Separate false-match metrics | PARTIAL | Evaluator reports false matches independently; no valid measured rate exists without adjudicated events. |
| 20 | Uncertainty intervals, coverage, and abstention reporting | COMPLETE | Evaluator computes Wilson intervals, coverage, abstention, and selective accuracy; no causal accuracy numbers are claimed. |
| 21 | Development and independent evaluation separation | COMPLETE | Frozen 19-case holdout remains untouched; public examples are identified as development/project-mapped data. |
| 22 | Verified-memory learning curve | BLOCKED | No independently adjudicated chronological cause/query set exists. No curve or values were fabricated. |
| 23 | Exasol-backed memory benchmark | PARTIAL | Read-only 0-active-history baseline measured median 51.627 ms and p95 64.753 ms. It is not a scale/throughput result; real reviewed histories are required for size checkpoints. |
| 24 | Database concurrency / larger-history validation | PARTIAL | Two simultaneous reviewers passed against Exasol; the read-only benchmark runner measured only N=0 because no active human-reviewed records exist. Larger histories/stress remain untested. |
| 25 | Existing API compatibility | COMPLETE | Existing API fields and routes were not changed by this task; API compatibility suite is included in `make verify`. |
| 26 | Timeouts, request IDs, and bounded database failure behavior | COMPLETE | Existing API safeguards remain; full test suite passes. |
| 27 | Memory token and reviewer authorization boundaries | PARTIAL | Configured bearer roles, reviewer-only decisions, and no self-approval exist; production identity management/rotation is outside current prototype. |
| 28 | Safe database-unavailable behavior | COMPLETE | Existing frontend/API report unavailable service state rather than presenting fabricated persisted memory. |
| 29 | Python regression and evaluation tests | COMPLETE | Targeted `test_benchmark_memory_exasol.py` + `test_verified_memory.py`: 18 passed. One `make verify`: 200 tests passed; challenge 16/16. |
| 30 | Frontend lint and production build | COMPLETE | The single `make verify` passed Oxlint and Vite production build; Vite emitted a non-failing >500 kB chunk advisory. |
| 31 | Hosted CI and exact runner parity | BLOCKED | No commit/push was made as instructed. Local checks passed; hosted CI was not triggered. |
| 32 | README, operational documentation, and judge preparation | PARTIAL | Live API/Exasol workflow is documented; a full browser rehearsal with a real authorized reviewer and demo recording remains outstanding. |
| 33 | Submission evidence and honest claims | PARTIAL | Existing submission verifier passes with `--allow-dirty`; historical media does not show a completed live memory workflow, and no new recording was made. |

## Live Exasol verification (2026-10-31)

The initially stopped Exasol Personal deployment was safely started. The full memory path was exercised against Exasol, including concurrent review, application restart, default-threshold retrieval, and audited revocation. A test-only confirmation was revoked after verification; no active test confirmation remains. Details and SQL evidence: [Exasol Verified Incident Memory runtime check](exasol-memory-e2e-2026-10-31.md).

## New change in this run

`app/memory.py` now conditionally transitions a submission from `pending`
inside the same transaction as reviewer work. If another reviewer has already
claimed the state, the transaction raises `MemoryConflict` and rolls back
before writing an audit or confirmation. This closes the stale-read path
identified during review. `tests/test_verified_memory.py` covers the losing
review claim. The mock regression does not substitute for a live Exasol
concurrency test.

## Verification and environment limits

- `.venv/bin/python -m pytest tests/test_benchmark_memory_exasol.py tests/test_verified_memory.py -q`: 18 passed.
- `make verify` (run once after this follow-up): 200 tests passed; predefined synthetic challenge 16/16; frontend Oxlint and Vite production build passed with a non-failing chunk-size advisory.
- `.venv/bin/python -m scripts.verify_submission --allow-dirty`: pass; no
  submission artifact failures.
- Exasol initially refused `127.0.0.1:8563` because Exasol Personal was stopped with stale deployment metadata. Safe `exasol start --wait-timeout-minutes 3` recovery succeeded; `make memory-check` then reported `pending: []`. Live lifecycle evidence and SQL: [Exasol runtime report](exasol-memory-e2e-2026-10-31.md).
- Docker Desktop server was available (Docker 29.9.2); Exasol Personal ran in its own local VM, with no Exasol Docker container.
- No live LLM, external participant study, or new independent holdout run was
  performed. No new result or accuracy claim is made.

## Judging criteria evidence

| Criterion | Weight | Current evidence and limitation |
|---|---:|---|
| Innovation and problem impact | 25% | Evidence-based incident classification and reviewed historical memory are implemented; measured engineer impact is absent. |
| Exasol usage | 25% | Existing analytical SQL and additive memory persistence were exercised against live Exasol; performance benchmark is not measured. |
| Technical excellence | 20% | Live two-reviewer race passed; larger-history stress, external validation, and hosted CI are unverified. |
| UX | 15% | Evidence comparison was exercised through the API; browser role workflow was not rehearsed. |
| Documentation | 10% | Runtime evidence and SQL outcomes are documented in the linked Exasol report; a live reviewer identity was not available. |
| Open-source quality | 5% | Repository retains license, contribution, and security guidance; no commit or push performed. |

## Evaluation and performance evidence follow-up (2026-10-31)

- **Human review:** Read-only Exasol audit inspection found only the `e2e-reviewer-test-b` approval and its `e2e-investigator-test` submission. Evidence references, checklist, decision rationale, reviewer identity, timestamps, confirmation audit, and revocation audit are present. These are test actors; there is no authorized human review to accept. Item 11 remains PARTIAL.
- **Benchmark protocol:** Added `reports/exasol-memory-benchmark-protocol-v1.md` and read-only runner `scripts/benchmark_memory_exasol.py`. It enforces exact active-history count, uses `record=False`, and checks repeated-result stability and no match-table writes. It does not create or clone confirmations.
- **Measured benchmark:** One empty-history run (0 active, 1 revoked; run ID 3673402), 3 warm-ups and 30 repetitions: median 51.627 ms, nearest-rank p95 64.753 ms, min 43.156 ms, max 68.460 ms, Python traced peak 349,780 bytes, process peak RSS 51,363,840 bytes. It returned zero candidates as expected. Exasol server memory and query-cache mode were not measured/verified. No increasing-history curve or improvement claim is available. Item 23 remains PARTIAL.
- **Public source candidates:** Added `reports/public-independent-incident-candidates-v1.md` with two new Airflow/dbt source candidates, project-assigned symptom-label proposals, upstream-resolution evidence where verified, and licensing limitations. An Airbyte issue was excluded from licensed corpus use because the repository uses ELv2 and issue-text terms are unclear. None was added to a corpus, used for tuning, or checked against hidden holdout labels.
- **Browser rehearsal:** Added `docs/verified-incident-memory-browser-rehearsal.md`. It requires a real authorized reviewer and covers submission, review, confirmation, persistence, app restart, retrieval, stale matches, revocation, and audit verification. No browser rehearsal was performed in this turn.
- Frozen evaluator assets and labels were not modified. No human study, independent evaluation, or scaling result is claimed.

## Documentation and reproducibility upgrade (2026-10-31)

- Replaced the long, stale root README with a judge-facing overview, quickstart, feature summary, distinct evidence table, Exasol contribution, and explicit limitations. Claims are cross-linked to their detailed reports.
- Added maintained guides for installation, configuration, architecture, data flow, Exasol setup, incident investigation, Verified Incident Memory, API, security, and troubleshooting. Existing lowercase architecture/API/Exasol/memory pages now redirect older links to the maintained uppercase guides. The frozen evaluation assets were not edited.
- Added `reports/reproducibility-and-evaluation.md` as a consolidated index for commands, dataset hashes and provenance, benchmark methods/results, memory measurement limits, and clean-clone status. It explicitly says a full clean-clone reproduction of the current revision was not completed and marks missing benchmark environment fields as not captured.
- Added `CHANGELOG.md`, contribution and security guidance, GitHub bug/feature issue templates, and a pull-request checklist.
- Documentation verification: 58 local Markdown links resolve across 31 selected README/docs/report files; database setup, memory migration, and memory benchmark CLI help commands exited successfully; all 25 API method/path entries (24 unique routes) in the reference match FastAPI OpenAPI; all 13 referenced Make targets exist. Read-only SHA-256 checks matched the published hashes for the frozen project/reviewer datasets, public corpora/registry, and frozen evaluator. No application implementation changed, so the already-recorded `make verify` result was not rerun during this docs-only change.
- Current-run clean-clone test: **not performed**. A historical checkout rehearsal applies to an earlier revision only. The consolidated report does not claim current clean-clone reproducibility.
