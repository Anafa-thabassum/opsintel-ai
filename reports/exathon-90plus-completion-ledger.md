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
| 3 | Public, provenance-tracked failure examples | PARTIAL | Existing ten-source GitHub issue collection and metadata manifest are documented; licensing and label adjudication limitations remain. |
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
| 16 | Verified-memory reviewer and investigator UI | PARTIAL | Existing role-aware submission/review UI remains; full browser interaction and live role workflow not rerun here. |
| 17 | Current and historical evidence comparison | COMPLETE | Similar-memory card displays the current investigation evidence separately from historical evidence. |
| 18 | Chronological leave-one-out / prequential evaluation | PARTIAL | Leakage-checked chronological evaluation harness exists; no adjudicated confirmation/query event stream is available. |
| 19 | Separate false-match metrics | PARTIAL | Evaluator reports false matches independently; no valid measured rate exists without adjudicated events. |
| 20 | Uncertainty intervals, coverage, and abstention reporting | COMPLETE | Evaluator computes Wilson intervals, coverage, abstention, and selective accuracy; no causal accuracy numbers are claimed. |
| 21 | Development and independent evaluation separation | COMPLETE | Frozen 19-case holdout remains untouched; public examples are identified as development/project-mapped data. |
| 22 | Verified-memory learning curve | BLOCKED | No independently adjudicated chronological cause/query set exists. No curve or values were fabricated. |
| 23 | Exasol-backed memory benchmark | PARTIAL | Exasol is reachable, but no controlled latency/throughput benchmark was run; the two issue-derived test rows are insufficient for performance claims. |
| 24 | Database concurrency / larger-history validation | PARTIAL | Two simultaneous reviewers were validated against live Exasol with one winner and no duplicate audit; larger histories, stress, and performance remain untested. |
| 25 | Existing API compatibility | COMPLETE | Existing API fields and routes were not changed by this task; API compatibility suite is included in `make verify`. |
| 26 | Timeouts, request IDs, and bounded database failure behavior | COMPLETE | Existing API safeguards remain; full test suite passes. |
| 27 | Memory token and reviewer authorization boundaries | PARTIAL | Configured bearer roles, reviewer-only decisions, and no self-approval exist; production identity management/rotation is outside current prototype. |
| 28 | Safe database-unavailable behavior | COMPLETE | Existing frontend/API report unavailable service state rather than presenting fabricated persisted memory. |
| 29 | Python regression and evaluation tests | COMPLETE | `.venv/bin/python -m pytest tests/test_verified_memory.py -q`: 16 passed. One `make verify`: 198 tests passed; predefined synthetic classifier challenge 16/16. |
| 30 | Frontend lint and production build | COMPLETE | The single `make verify` run passed Oxlint and Vite production build; Vite emitted its non-failing >500 kB chunk advisory. |
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

- `.venv/bin/python -m pytest tests/test_verified_memory.py -q`: 16 passed.
- `make verify` (run once): 198 tests passed; predefined synthetic challenge 16/16; frontend Oxlint and Vite build passed with a non-failing chunk-size advisory.
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
