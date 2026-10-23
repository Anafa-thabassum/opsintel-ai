# Judging evidence map

This page maps each ExaThon criterion to evidence a judge can verify. It is not
a self-awarded score.

| Criterion | Evidence | Best demo moment | Claim boundary |
|---|---|---|---|
| Innovation and problem impact (25%) | Clear on-call engineer problem, evidence-first workflow, ten frozen study cases and a counterbalanced four-participant protocol | Open an incident and move from row discrepancy to next action | 0/40 trials recorded across 0/4 participants; no time-saving result yet |
| Effective use of Exasol Personal (25%) | Exasol-backed runs and logs, analytical window-function view, hierarchical `CONNECT BY` cascade, bulk import path, and controlled 1M/10M comparison | Show three downstream failures within the 120-minute correlation window, then the honest benchmark chart | Temporal correlation does not confirm causation; DuckDB was faster locally, with no Exasol speed or concurrency claim |
| Technical excellence (20%) | FastAPI, parameterized queries, timestamped evidence, claim-level LLM references and excerpts, 137 tests, a 27-case versioned project-authored holdout, a licensed 9-case public-message corpus, CI, frontend lint and production build | Run `make verify`, `make holdout`, and `make public-evaluate`; use `make smoke` only on an authorized disposable database | Public-corpus labels are project-authored; external holdout has 0 cases from 0 authors; live LLM quality and v1 holdout freeze order are not independently proven |
| Solution design and UX (15%) | Responsive incident dashboard, failed-run versus last-success comparison, three-column observation/candidate/verification view, evidence IDs, safe next action and session review state | Select `daily_sales_import`, compare it with the last success, then move through the decision view | Review state is demo-session only; accessibility has not received an external audit |
| Documentation and reproducibility (10%) | README, database setup, deployment guide, evaluation report, raw benchmark, demo script, submission package, and Batch 6 clean-clone report | Follow the run guide from setup through verification and process startup | Fresh isolated macOS clone passed; Exasol-backed workflow and a second-machine rehearsal remain unverified |
| Open-source quality (5%) | MIT licence, CI, contributing guide, security policy and public repository | Open the repository root | Verify the final commit and public links again after the video replacement |

## Judge path in five minutes

1. Read the README problem statement and Exasol section.
2. Open the dashboard and select `daily_sales_import`.
3. Confirm that every observation names its source and the confirmed root cause
   is `None`.
4. Open `sql/analysis/pipeline_health_features.sql`.
5. Open `reports/exasol-benchmark.json` and `reports/evaluation.md`.
