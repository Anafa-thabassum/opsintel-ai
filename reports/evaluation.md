# OpsIntel AI — Evaluation Report

## Objective

Evaluate whether OpsIntel AI classifies common data-pipeline failure evidence
without converting unsupported possibilities into confirmed root causes.

## Automated verification

- Automated tests: **60 passed**
- Frontend lint: **passed with no warnings**
- Frontend production build: **passed**
- Database: Exasol Personal
- API: FastAPI
- Dashboard: React and Vite

Run the checks with:

```bash
make verify
```

The automated suite also covers delayed runs, excess or duplicate rows,
conflicting completion signals, timestamped history retrieval, malformed LLM
output, unavailable model calls, and rejection of unknown evidence references.

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

## Frozen synthetic holdout

A separate versioned dataset contains 27 cases that do not appear in the
regression suite. It covers all nine classifier outcomes with three cases per
expected category. The expected labels were frozen before the evaluator ran,
and the classifier was not changed between the freeze and the recorded result.

| Measure | Result |
|---|---:|
| Cases | 27 |
| Categories | 9 |
| Correct classifications | 27/27 |
| Accuracy on this dataset | 100.0% |

The dataset SHA-256, classifier SHA-256, classifier commit, category totals,
and per-case predictions are published in
[`reports/frozen-holdout-v1.md`](frozen-holdout-v1.md) and
[`reports/frozen-holdout-v1.json`](frozen-holdout-v1.json). Run `make holdout`
to reproduce the evaluation.

The project team authored this synthetic holdout. It is stronger evidence than
rerunning the implementation's regression cases, but it is not an independent
or production accuracy estimate. The empty reviewer template remains available
for a genuinely external evaluation.

## Exasol analytical validation

The demo dataset contains four days of healthy pipeline history followed by
four representative incidents. Exasol calculates completeness, previous-run
status, rolling actual-row baselines, and rolling failure rates through
`OPSINTEL.PIPELINE_HEALTH_FEATURES`.

Run `make exasol-proof` with Exasol Personal active to print the exact history
and log-evidence rows for the selected demonstration incident. This command is
the reproducible live-query proof; no result is recorded when Exasol is not
running.

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
- The regression and frozen holdout sets are small and are stored with the
  implementation.
- The project team authored the frozen holdout; an independent reviewer result
  remains pending.
- Keyword rules do not establish semantic understanding.
- The optional LLM summary has not received an independent quality evaluation.
- Human investigation-time impact remains unmeasured; the repository includes
  a protocol, recording template, and deterministic result summarizer.
- Candidate explanations remain unconfirmed until an engineer verifies them.
- Concurrency, production infrastructure, and real orchestrator integrations
  have not been evaluated.
