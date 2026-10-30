# OpsIntel implementation and verification — 2026-10-31

## Result

OpsIntel now has a second, real public-data investigation mode. The official
GitHub issue API supplied nine Apache Airflow and one dbt issue; their short,
screened diagnostic excerpts and provenance were stored in Exasol and queried
through new read-only FastAPI endpoints. The React workspace supports source
and category filters, text search, source links, symptom signals, unresolved
outcomes, provenance, and unverified text neighbours. The existing synthetic
pipeline demo, deterministic classifier, verified-memory workflow and Exasol
analytical views remain in place.

This is a working prototype with important validation gaps. No new human
confirmation, independent causal holdout, participant study or memory learning
curve was produced. The public issue comparison uses project-authored labels.

## Six priorities

| Priority | Status | Evidence and limit |
|---|---|---|
| Classifier intelligence | Partial | Existing deterministic normalization, structured signals, multiple symptoms, scoped conflicts and abstention retained. 193 local Python tests and 16/16 predefined synthetic cases pass; no fresh independent validation. |
| Verified Incident Memory | Partial | Existing additive Exasol tables, separated investigator/reviewer grants, checklist, audit, correction/revocation and candidate retrieval remain. Prior rollback-only live SQL rehearsal passed; no human-confirmed record was retained. |
| Real public data | Complete for one ingestion path | Ten official GitHub issues fetched and loaded into `OPSINTEL.PUBLIC_INCIDENTS`; live search, pagination, analytics, evaluation and UI investigation worked. Issue-text licensing and label quality remain limited. |
| Evaluation and impact | Partial | Public project-label comparison 7/10, unresolved 6/10, source-reference coverage 10/10. False-match rate, memory retrieval accuracy, learning curve and human time savings are unmeasured. |
| UI and documentation | Partial | New responsive public workspace and navigation integrated with the existing polished synthetic dashboard. Desktop dashboard and narrow public viewport inspected. Dedicated dependency graph, broad analytics workspace, automated frontend interaction tests and fresh demo recording remain absent. |
| Open source and CI | Partial | Local full verification, submission verifier, secret-pattern scan and offline npm production-dependency audit pass. Hosted GitHub Actions cannot run for uncommitted changes. |

## Public data and provenance

- Registry: `evaluation/public_source_registry_v1.json`, pinning nine Airflow
  issue IDs and one dbt issue ID. The historical `dbt-labs/dbt-core` link now
  resolves through the canonical `dbt-labs/dbt` API repository.
- Live retrieval: the official GitHub issue API returned all ten records during
  initial ingestion. Source identity, original URL, created/updated time,
  collection time, excerpt origin and SHA-256 of the full source body are kept
  in Exasol. Full bodies are not stored.
- Licence: Airflow and dbt source code uses Apache-2.0. GitHub issue text is
  user-generated; no separate redistribution licence was established. Only
  short screened excerpts are cached locally. LogHub HDFS was excluded because
  its terms and raw-log privacy require further review.
- Reproducibility: additive migration `002_public_incidents.sql`, registry and
  `python -m scripts.ingest_public_issues`. Nine records were unchanged on a
  repeat fetch. The last dbt refresh received GitHub HTTP 403 with the
  unauthenticated hourly rate limit at zero; its previously cached record
  remained available. The CLI now reports reset time or optional `GITHUB_TOKEN`
  and exits nonzero rather than silently reporting success.
- Evaluation: 10 collected, 10 project-labelled, 0 independently adjudicated,
  7 exact category matches, 6 unresolved, 100% source-reference coverage, and
  no causal false-match measurement. Three `ModuleNotFoundError` examples have
  project `dependency_failure` labels, but missing Python modules do not by
  themselves prove a failed required upstream pipeline dependency. The current
  unresolved predictions are therefore defensible pending independent label
  review. See `reports/public-data-evaluation.md` for every source.

## Exasol and memory boundaries

Exasol executes existing rolling pipeline health window queries (`LAG`, row
baselines, completeness and failure rates), dependency `CONNECT BY` analysis,
durable memory/audit storage, active candidate filtering, and the new public
issue search, pagination and grouped source/category counts. Python performs
evidence screening, deterministic classification and token-pair similarity.
The ten-row public collection is not a performance benchmark.

Verified memory retrieval still returns historical **candidates** only. An
authorized reviewer must approve cause-specific evidence; the classifier and
LLM cannot confirm a cause. The existing live Exasol migration and rollback
rehearsal establishes database compatibility, but does not prove real causal
accuracy or a completed human reviewer workflow. `reports/memory-matching-benchmark.md`,
`reports/learning-curve-evaluation.md` and `reports/business-impact-study.md`
correctly publish no measured result yet.

## Verification

| Check | Result |
|---|---|
| `.venv/bin/python -m pytest -q` | 193 passed, 0 failed, 0 skipped |
| `.venv/bin/python -m tests.run_evaluation` | 16/16 predefined synthetic cases; not production accuracy |
| `npm run lint` and `npm run build` | Pass; Vite still issues a non-failing ~646 kB main-chunk advisory |
| `.venv/bin/python -m scripts.verify_submission --allow-dirty` | Pass; historical submission media remain dated |
| Live Exasol migration and public queries | Pass on local Exasol Personal; ten cached issues |
| Public UI | Search, filters, source links, detail, textual neighbour navigation and narrow viewport inspected |
| Offline `npm audit --omit=dev` | Zero production dependency advisories in the available offline audit data |
| Secret-pattern scan and `git diff --check` | No matching tracked secret pattern; no whitespace error |

Protected hashes remain:

| Asset | SHA-256 |
|---|---|
| `evaluation/independent_holdout_v1.csv` | `64d766d4782ee94223796e91d79c35fb359d3dcd9de414b1b8ebed41afacf71b` |
| `evaluation/public_development_corpus_v2.jsonl` | `2b16264d2954e57f9202dc3d9fa2e00e04d466598748caeb31e158381c331a5e` |
| `scripts/evaluate_holdout.py` | `c07b1f2ddcc3b5e1f11447bf8f7aa98501c2f99c5d8f3657106945254d9feb75` |
| `reports/independent-holdout-v1.json` | `79b54ba0825313089ed44b13d9ae87c7f3edcbbc5186658ed6a240fc9001235a` |
| `reports/independent-holdout-v1.md` | `6a9e58bc1322e591eb8bbe43e630c57bebd762c3f45c2bdc35b70de5598824c2` |

Historical 4/19 independent baseline and same-reviewer 15/19 comparison were
not rerun, relabelled or presented as fresh validation. The development corpus
V2 was not changed. Historical reports, submission assets and frozen evaluator
were not edited.

## Files and release state

New: `app/public_data.py`, `sql/migrations/002_public_incidents.sql`, public
source registry, ingestion/evaluation scripts, `frontend/src/PublicData.jsx`
and CSS, public-data docs and report, public-data tests. Updated: `app/main.py`
(read-only routes), `scripts/setup_database.py` (reset guard),
`frontend/src/App.jsx` (navigation), README, Makefile, `.env.example`, and
architecture/API/Exasol/evaluation/demo docs. Existing Exasol integration and
classifier implementation were not changed.

Branch: `main`. Working tree: dirty by design; no commit or push. The local
checks above do not prove the hosted GitHub Actions run for these changes.

## Conservative judging estimate

| Criterion | Estimate | Basis |
|---|---:|---|
| Innovation and problem impact / 25 | 18 | Evidence-first investigation and governed memory, without measured human benefit |
| Exasol use / 25 | 20 | Live analytical SQL, memory schema and public search; no public scale benchmark |
| Technical excellence / 20 | 15 | Passing local suite and provenance checks; no hosted CI on this diff |
| Design and UX / 15 | 11 | Coherent dashboard and new public workspace; some requested dedicated views absent |
| Documentation / 10 | 8 | Reproducible local commands and honest limits; demo media dated |
| Open source / 5 | 4 | MIT, contribution/security guidance and CI workflow; uncommitted changes |
| **Total / 100** | **76** | Subjective estimate, not an organizer score |

## Remaining manual work

An authorized human reviewer must provide and verify a real source-backed
causal case before a retained memory confirmation is demonstrated. Independent
adjudicators and participant investigators are required for memory accuracy
and time-impact claims. The owner must review this diff, run hosted CI after
an approved commit, and record a new demo using observed results.
