# Judging evidence map

This page maps each ExaThon criterion to evidence a judge can verify. It is not
a self-awarded score.

| Criterion | Evidence | Best demo moment | Claim boundary |
|---|---|---|---|
| Innovation and problem impact (25%) | Clear on-call engineer problem, evidence-first workflow, executable impact-study protocol and recording template | Open an incident and move from row discrepancy to next action | Human time savings remain unmeasured until participants complete the study |
| Effective use of Exasol Personal (25%) | Exasol-backed runs and logs, analytical window-function view, live telemetry, one-million-row benchmark | Show the trend, then the analytical SQL and benchmark slide | Local single-user benchmark only |
| Technical excellence (20%) | FastAPI, parameterized queries, timestamped evidence, validated LLM references, 60 tests, CI, frontend lint and production build | Run `make verify` or open CI | Synthetic prototype, not production infrastructure |
| Solution design and UX (15%) | Responsive incident dashboard, recent-run timeline, timestamped evidence trail, database source labels, safe next action and session review state | Select `daily_sales_import` and scroll through observations | Review state is demo-session only; accessibility has not received an external audit |
| Documentation and reproducibility (10%) | README, database setup, deployment guide, evaluation report, raw benchmark, demo script and submission package | Follow the run guide from setup to `/health` | Clean-clone rehearsal on a second machine remains recommended |
| Open-source quality (5%) | MIT licence, CI, contributing guide, security policy and public repository | Open the repository root | Final local changes still need to be pushed |

## Judge path in five minutes

1. Read the README problem statement and Exasol section.
2. Open the dashboard and select `daily_sales_import`.
3. Confirm that every observation names its source and the confirmed root cause
   is `None`.
4. Open `sql/analysis/pipeline_health_features.sql`.
5. Open `reports/exasol-benchmark.json` and `reports/evaluation.md`.
