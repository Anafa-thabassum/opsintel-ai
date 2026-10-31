# OpsIntel AI — final ExaThon execution review (2026-10-31)

## Executive result

This task updated the React shell, public-data error handling, project-facing
claims, the editable pitch deck and PDF, submission guidance, and the submission
verifier. The deterministic classifier, memory API implementation, database
schema, public datasets, and evaluation assets were not changed in this task.

Local verification passed: 197 Python tests, 16/16 predefined synthetic
challenge cases, frontend lint, production build, and the submission verifier.
The build emits a non-failing 657.66 kB main-chunk size advisory. The app's
home page is reachable locally. Exasol-backed pages return HTTP 503 because no
local Exasol service is available. No database workflow, retained cause
confirmation, new memory retrieval, new independent evaluation, participant
study, live LLM call, or new video recording is claimed.

The referenced primary specification, `OpsIntel_Verified_Incident_Memory.pdf`,
was not found in the repository. This review therefore checks the implemented
memory workflow against the approved design addendum and the requirements
reproduced in the user's request; it cannot certify document-level coverage of
the missing PDF.

## Requirement status

| Area | Status | Evidence and boundary |
|---|---|---|
| UI and navigation | PARTIAL | Updated responsive shell, collapsible sidebar, mobile drawer, theme styling, route navigation, public-data error/loading/empty states, local public scorecard, and client-side incident search/sorting/paging. Home page was opened and visually inspected; prior route checks are documented in the earlier execution report. Dashboard/private demo entry requires a session; Exasol routes currently return 503, so all underlying journeys cannot be verified live. Settings remain hidden because no settings feature exists. |
| Verified Incident Memory | PARTIAL | Existing API and Exasol schema support investigator submissions, separate authorized review, checklists, audit records, correction/revocation, and retrieval as an unconfirmed candidate. Full Python suite passes. The local service was unavailable, so submit → approve → restart → retrieve → reject/correct/revoke was not exercised against Exasol in this task. Similarity scoring runs in the application after Exasol filters active records; there is no Exasol UDF and the score is not a probability. |
| Public data | PARTIAL | Existing ten-case Airflow/dbt issue path and public scorecard remain separate from synthetic telemetry. The 7/10 figure is agreement with project labels, not independent accuracy. GitHub issue text has no separately established redistribution licence; only short excerpts are cached. The current public-data page correctly reports unavailable Exasol data rather than displaying fabricated totals. |
| Evaluation integrity | COMPLETE | Frozen 19-case CSV, V2 development corpus, evaluator, and historical reports retain their recorded hashes. No holdout was tuned or rerun in this task. The original baseline remains 4/19. The 15/19 comparison uses the same 19 labels and is not independent validation. |
| Evaluation breadth | PARTIAL | The existing synthetic challenge run returns 16/16. The public issue comparison is 7/10 on project-authored mappings; no external adjudication, fresh independent holdout, measured learning curve, memory false-match rate, or user-impact study is available. |
| Pitch deck and PDF | COMPLETE | Updated 11-slide PPTX and matching 11-page PDF. Both show the separate reviewer gate, application-side matching boundary, current 197-test run, public-label limits, same-holdout caveat, and no measured user savings. PPTX package/layout/font checks passed; rendered slides were reviewed. Deck does not stage a successful live memory confirmation. |
| Demo video | BLOCKED | The existing MP4 is 154.445 seconds and under the 3-minute limit, but it is a historical recording and does not show verified memory. A new honest memory walkthrough needs an authorized Exasol instance, distinct investigator/reviewer identities, and supported causal evidence. `submission/video-narration.txt` is now clearly a draft script, not a recording transcript. |
| Documentation and Q&A | PARTIAL | README, submission README/checklist, judge Q&A, approved design addendum, and demo script were reconciled with the current public scorecard, test count, and memory policy. The referenced feature-spec PDF is missing, current Exasol setup is unavailable, and hosted CI was not run on this dirty tree. |
| Open-source release | PARTIAL | MIT licence, CONTRIBUTING.md, SECURITY.md, public repository references, and reproducible local commands exist. The current working tree is uncommitted; hosted CI on this exact tree and a clean-room Exasol rehearsal remain unverified. |

## Approved memory design vs. primary specification

The addendum now records role-based confirmation and all seven cause-specific
criteria as approved design policies, while explicitly stating that they are
not empirically validated. Implementation keeps symptoms separate from
candidate causes and confirmed causes; requires source-backed symptom and
causal evidence; blocks approval on a classifier conflict or missing checklist
criterion; records reviewer identity, rationale, timestamp, and audit history;
and presents retrieved records as candidates. It never treats a similarity
score as confidence or automatically repairs a pipeline.

| Memory requirement from the supplied request | Status | Evidence |
|---|---|---|
| Versioned log and structured fingerprint | COMPLETE | `app/fingerprint.py`, `docs/incident-fingerprinting.md`; versioned token-pair similarity plus structured agreement/conflict features. |
| Exasol is authoritative for confirmed memory | COMPLETE in design/code | `app/memory.py`, schema/migrations, and `docs/verified-incident-memory.md`; live persistence was not rechecked because Exasol is unavailable. |
| Exasol-native similarity/UDF | PARTIAL | Exasol filters active, non-self candidates; Python computes bounded similarity over at most 500 rows. The implementation and README accurately disclose no UDF. |
| Separate investigator and reviewer with no self-approval | COMPLETE in code; live workflow PARTIAL | Configured role grants and differing actor IDs are enforced; reviewer checklist is mandatory. No live transaction was performed today. |
| Confirmation, restart persistence, retrieval, and engineer decision | BLOCKED for this run | Requires a running authorized Exasol service and a source-backed confirmation. No confirmation was fabricated. |
| The primary PDF's complete requirements | BLOCKED | `OpsIntel_Verified_Incident_Memory.pdf` is absent, so direct requirement-by-requirement comparison is impossible. |

## Public-data and claim boundaries

- Ten public issue records are project-mapped; the 7/10 score is compatibility
  with those mappings, not a gold-label estimate.
- Three `ModuleNotFoundError` cases labelled `dependency_failure` remain
  questionable because a missing module alone does not prove a failed required
  upstream dependency.
- Repository code licences do not automatically establish licences for
  user-authored issue text. The corpus preserves provenance and short screened
  excerpts; redistribution rights remain uncertain.
- The existing public-data workspace needs Exasol's populated cache. With the
  service absent, the route reports 503 and does not substitute synthetic
  records.
- The new recording script explicitly separates the historical video from a
  future walkthrough and tells the presenter to use `needs_more_evidence` when
  causal criteria are not met.

## Official ExaThon criteria compliance

The official event page says public or synthetic data only, requires Exasol
Personal, an MIT/Apache-2.0 public repository, a pitch deck and a demo of at
most three minutes, and publishes the 25/25/20/15/10/5 judging weights. The
Stage 2 format is 15 minutes plus 5 minutes of Q&A. See the
[official ExaThon India 2026 requirements](https://www.exasol.com/events/exathon-india-2026/).

| Criterion | Weight | Status | Evidence and remaining gap |
|---|---:|---|---|
| Innovation and problem impact | 25% | PARTIAL | Defines on-call data engineers and fragmented pipeline evidence; traceable investigation and governed memory distinguish the workflow. No measured time, financial, or user benefit. |
| Effective use of Exasol Personal | 25% | PARTIAL | SQL evidence includes `LAG`, rolling completeness/failure baselines, `CONNECT BY`, public issue filtering, and memory persistence schema. The recorded local benchmark is transparent and shows DuckDB faster at 10M rows. Current Exasol service and full memory demo are unavailable. |
| Technical excellence | 20% | PARTIAL | 197 tests and 16/16 synthetic challenge cases pass; deterministic classification, evidence references, abstention, auth gates, and safe LLM boundary are documented. No current live Exasol lifecycle, hosted CI, live LLM, or independent causal validation. |
| Solution design and user experience | 15% | PARTIAL | Responsive home/public surfaces, search, filters, explicit 503 states, memory candidate language, and navigation are present. No complete live walkthrough of all authenticated/data-backed routes in this environment. |
| Documentation and reproducibility | 10% | PARTIAL | README, setup, SQL, evaluation methodology, submission guide, and Q&A are present and reconciled. Primary memory PDF missing; new video not recorded; clean-room Exasol rehearsal outstanding. |
| Open-source quality | 5% | PARTIAL | MIT licence, CONTRIBUTING.md, SECURITY.md, and public GitHub workflow exist. No commit/push was performed; hosted CI on this exact working tree remains unverified. |

## Conservative score estimate

**72/100 (subjective estimate, not an organizer score):** innovation 17/25,
Exasol 17/25, technical 15/20, UX 11/15, documentation 8/10, and open-source
quality 4/5. The biggest score limits are the missing live memory demonstration,
no new independent validation or user study, and no hosted CI result for this
working tree.

## Verification performed

| Check | Result |
|---|---|
| `make verify` | PASS — 197 passed, 0 failed; 16/16 predefined synthetic challenge cases; frontend lint passed; production build passed with the 657.66 kB advisory. |
| `python -m scripts.verify_submission --allow-dirty` | PASS — 197 test count, video 154.445 s, 11 slides, 11 PDF pages, no submission-asset failures. |
| `make submission-check` | BLOCKED only by its clean-working-tree requirement; it reports “Working tree is not clean.” The allow-dirty content check passed. No commit/push was made. |
| PPTX finalization | PASS — 11 slides, package integrity, layout and typography checks; first-party re-import passed. |
| `git diff --check` | PASS. |
| Browser UI | Home page rendered and inspected. Public-data route rendered its Exasol-unavailable/503 state; the email-gated synthetic workspace was not entered. |
| Exasol/live memory | NOT RUN — local Exasol service unavailable. No migration, ingestion, benchmark, database operation, or live LLM call was performed in this task. |
| Hosted GitHub Actions | NOT RUN — no commit or push was made. |

Protected asset hashes after the work:

| Asset | SHA-256 |
|---|---|
| `evaluation/independent_holdout_v1.csv` | `64d766d4782ee94223796e91d79c35fb359d3dcd9de414b1b8ebed41afacf71b` |
| `evaluation/public_development_corpus_v2.jsonl` | `2b16264d2954e57f9202dc3d9fa2e00e04d466598748caeb31e158381c331a5e` |
| `scripts/evaluate_holdout.py` | `c07b1f2ddcc3b5e1f11447bf8f7aa98501c2f99c5d8f3657106945254d9feb75` |
| `reports/independent-holdout-v1.json` | `79b54ba0825313089ed44b13d9ae87c7f3edcbbc5186658ed6a240fc9001235a` |
| `reports/independent-holdout-v1.md` | `6a9e58bc1322e591eb8bbe43e630c57bebd762c3f45c2bdc35b70de5598824c2` |

## Changed files

- **UI:** `frontend/src/App.jsx`, `frontend/src/App.css`,
  `frontend/src/PublicData.jsx`, `frontend/src/PublicData.css`.
- **Design and user guidance:** `reports/classifier-design-addendum-v1.md`,
  `README.md`, `docs/judge-qa.md`, `docs/submission-checklist.md`,
  `submission/README.md`, `submission/video-narration.txt`.
- **Submission checks:** `scripts/verify_submission.py`,
  `tests/test_submission_verification.py`.
- **Submission media:** `submission/opsintel-ai-pitch-deck.pptx` and
  `submission/opsintel-ai-pitch-deck.pdf`.

No classifier implementation, Exasol schema, frozen evaluation data, historic
evaluation report, benchmark result, or submission video was modified. No
commit or push was made.
