# OpsIntel AI — Evaluation Report

## Objective

Evaluate whether OpsIntel AI classifies common data-pipeline failure evidence
without converting unsupported possibilities into confirmed root causes.

## Automated verification

- Automated tests: **45 passed**
- Frontend lint: **passed with no warnings**
- Frontend production build: **passed**
- Database: Exasol Personal
- API: FastAPI
- Dashboard: React and Vite

Run the checks with:

```bash
python -m pytest -q
python -m tests.run_evaluation
cd frontend && npm run lint && npm run build
```

## Synthetic challenge set

The challenge set contains 16 predefined cases across six expected outcomes.
It includes exact signals, paraphrases, benign timeout configuration, and
unknown evidence.

| Expected outcome | Correct | Total |
|---|---:|---:|
| Dependency failure | 3 | 3 |
| Early termination | 3 | 3 |
| Incomplete data | 2 | 2 |
| Schema mismatch | 3 | 3 |
| Timeout | 3 | 3 |
| Unclassified | 2 | 2 |
| **Total** | **16** | **16** |

The measured result is **16/16 on this predefined synthetic challenge set**.
It is a reproducible regression benchmark, not a production accuracy claim.

## Exasol analytical validation

The demo dataset contains four days of healthy pipeline history followed by
four representative incidents. Exasol calculates completeness, previous-run
status, rolling actual-row baselines, and rolling failure rates through
`OPSINTEL.PIPELINE_HEALTH_FEATURES`.

## Reproducible scale benchmark

`python -m scripts.benchmark_exasol` creates an isolated temporary schema,
imports deterministic history, executes the Exasol window-feature and daily
aggregation query, and removes the schema. On the recorded local run:

| Measure | Result |
|---|---:|
| Synthetic pipeline runs | 1,000,000 |
| Pipelines | 20 |
| Import time | 3.025 seconds |
| Query repetitions | 7 |
| Median analytical query | 473.209 ms |
| p95 analytical query | 503.947 ms |

The complete samples and environment are preserved in
[`reports/exasol-benchmark.json`](exasol-benchmark.json). This is a local,
single-user measurement, not a production throughput or concurrency claim.

## Limitations

- The scenarios and logs are synthetic.
- The challenge set is small and is stored with the implementation.
- Keyword rules do not establish semantic understanding.
- Candidate explanations remain unconfirmed until an engineer verifies them.
- Concurrency, production infrastructure, and real orchestrator integrations
  have not been evaluated.
