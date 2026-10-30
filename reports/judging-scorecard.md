# Judging evidence map

This page maps each ExaThon criterion to evidence a judge can verify. It is not
a self-awarded score.

| Criterion | Evidence | Best demo moment | Claim boundary |
|---|---|---|---|
| Innovation and problem impact (25%) | Clear on-call engineer problem, evidence-first workflow, ten frozen study cases and a counterbalanced four-participant protocol | Open an incident and move from row discrepancy to next action | 0/40 trials recorded across 0/4 participants; no time-saving result yet |
| Effective use of Exasol Personal (25%) | Exasol-backed runs and logs, analytical window-function view, hierarchical `CONNECT BY` cascade, bulk import path, and controlled 1M/10M comparison | Show three downstream failures within the 120-minute correlation window, then the honest benchmark chart | Temporal correlation does not confirm causation; DuckDB was faster locally, with no Exasol speed or concurrency claim |
| Technical excellence (20%) | FastAPI, parameterized queries, timestamped evidence, claim-level LLM references and excerpts, 137 tests, a 27-case versioned project-authored holdout, a frozen 19-case reviewer holdout, a public-data scorecard over cited Airflow/dbt issue excerpts, CI, frontend lint and production build | Open `#/scorecard` from the landing page to inspect each public source, licence, label mapping, and classifier result; reproduce with `make public-evaluate-v2` | Reviewer holdout scored 4/19 (21.1%) and is not a production accuracy estimate; public-corpus labels are project mappings, not independent ground truth; live LLM quality remains unverified |
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

## Public-data scorecard

The landing page's **View public-data scorecard** link opens `#/scorecard`, a
read-only view evaluated from `evaluation/public_failure_corpus_v2.csv`. The
ten excerpts come from public Apache Airflow and dbt issue records. Each case
shows its source URL, repository licence URL, original source category, OpsIntel
category mapping, mapping rationale, and the current classifier result. The
published project-mapped score is 7/10; it measures compatibility with this
small corpus and does not establish production accuracy. The separate Exasol
incident demo still uses synthetic data and is labelled as such.
