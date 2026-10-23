# OpsIntel AI — Evaluation Report

## Objective

Evaluate whether OpsIntel AI classifies common data-pipeline failure evidence
without converting unsupported possibilities into confirmed root causes.

## Automated verification

- Automated tests: **137 passed**
- Frontend lint: **passed with no warnings**
- Frontend production build: **passed**, with a non-failing 616.60 kB
  main-chunk advisory
- Database: Exasol Personal
- API: FastAPI
- Dashboard: React and Vite

Run the checks with:

```bash
make verify
```

The automated suite also covers delayed runs, excess or duplicate rows,
conflicting completion signals, timestamped history retrieval, malformed LLM
output, unavailable model calls, claim-level evidence references, dependency
cascade responses, and Airflow/dbt JSON normalization. It also verifies an
explicit unresolved result when evidence is insufficient and a complete
deterministic response when the optional model is disabled, times out, or is
unavailable.

## Failed-run comparison and evidence tracing

The investigation endpoint now compares the selected failure with the most
recent successful run for the same pipeline. It reports expected rows, actual
rows, completeness change, a historical successful-run baseline, and log
messages that appear only in the failed run. Each non-zero difference lists the
candidate explanations that share its cited evidence references.

A live Exasol smoke run on 19 October 2026 reset and reseeded the synthetic
schema, then investigated run `1` against successful run `113`. The API returned
an actual-row change of `-20`, a completeness change of `-20` percentage points,
three new or changed log messages, and a four-run successful baseline. The
confirmed root cause remained unset.

Run the same database/API check with:

```bash
make smoke
```

This command resets the synthetic `OPSINTEL` schema and must run only against
an explicitly authorized disposable Exasol deployment.

The deterministic classifier covers missing evidence, conflicting completion
signals, duplicate-row patterns, and unknown logs. Candidate explanations carry
exact run or log references. An unfamiliar log without sufficient support
returns `resolution_status: unresolved` and a diagnostic next step instead of
an invented cause. Its qualitative confidence is `medium` only for one explicit
log-phrase match and `low` for row-count-only, competing, conflicting, or
unclassified evidence. It does not emit uncalibrated probability percentages.
When several categories match, the API returns every match and the documented
precedence reason used to select the displayed category.

## Optional LLM validation

The configured `gpt-6-luna` identifier is documented in the official OpenAI
model catalog. The automated tests cover disabled configuration, missing
credentials, connection errors, timeouts, malformed structured output, unknown
evidence references, rate limiting, incomplete responses, fabricated numeric
facts, unsafe confirmation language, unresolved cases, and ungrounded
individual claims. Every accepted claim requires an exact excerpt from each
cited observation, and its facts are checked only against those cited
observations. Evidence gaps are restricted to exact server-owned options for
the deterministic category. In every failure mode, the complete deterministic
investigation remains available.

No live request was performed because explicit authorization for possible API
cost was not supplied. Model entitlement, real-model grounding quality, usage,
and cost therefore remain unverified. The 14/14 focused tests use mocked
responses and are not evidence of live model access. See
[`reports/llm-evaluation.md`](llm-evaluation.md) for the separate Batch 7
record.

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

## Versioned project-authored holdout

A separate versioned dataset contains 27 cases that do not appear in the
regression suite. It covers all nine classifier outcomes with three cases per
expected category. The recorded classifier hash matches the pre-existing
`eb7a2d8` implementation commit. The dataset and result report first entered Git
history together in `73c44ed`, so the repository does not independently prove
that the labels were committed before scoring.

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

## Licensed public-message compatibility corpus

Nine short framework-generated failure messages from Apache Spark, Apache
Airflow, and dbt-common were evaluated with per-case source and Apache-2.0
licence URLs. The current classifier matched **6/9 (66.7%)**. All three misses
are published: Spark executor shutdown, Spark shuffle fetch failure, and
Airflow upstream failure vocabulary currently resolve to `unclassified` rather
than the project-labelled category. No root cause is confirmed for those misses.

See [`reports/public-corpus-v1.md`](public-corpus-v1.md), the machine-readable
[`reports/public-corpus-v1.json`](public-corpus-v1.json), and
[`evaluation/public_failure_corpus_v1.csv`](../evaluation/public_failure_corpus_v1.csv).
Run `make public-evaluate` to reproduce the report. This small corpus uses
project-assigned labels and is a compatibility check, not an independent or
production accuracy estimate.

The supplied issue-linked starter is preserved separately as
[`evaluation/public_failure_corpus_v2.csv`](../evaluation/public_failure_corpus_v2.csv).
It contains 10 Airflow/dbt cases and scores **7/10** after mapping its richer
source labels into the supported OpsIntel taxonomy. Reproduce it with
`make public-evaluate-v2`. The mapping is explicit in the CSV; it does not
convert this project-labelled check into independent accuracy.

## Independent reviewer workflow

The external-reviewer template remains intentionally header-only: **0 cases
from 0 external reviewers have been recorded**, so independent validation is
still pending and no accuracy result is claimed.

The Batch 4 evaluator now requires 15–20 cases from two or three pseudonymous
external reviewers. Each case carries a dataset version, referenced evidence,
expected findings, expected uncertainty, and explicit reviewer provenance.
Before scoring, one Git ref must freeze the dataset, deterministic classifier,
and evaluator/scoring implementation. The generated JSON and Markdown reports
record the UTC evaluation time, hashes and versions, completed cases, exact
category matches, incorrect findings, unresolved predictions, missing labels,
input-evidence traceability, and whether the output remained unconfirmed.

Scoring is declared before evaluation: only an exact category match receives
credit; there is no partial category credit. Missing labels are reported and
excluded from accuracy. An `unclassified` prediction remains unresolved and is
never rewarded as a confirmed cause. See
[`evaluation/README.md`](../evaluation/README.md) for the schema and freeze
procedure.

## Exasol analytical validation

The demo dataset contains four days of healthy pipeline history followed by
eleven representative incidents. Exasol calculates completeness, previous-run
status, rolling actual-row baselines, and rolling failure rates through
`OPSINTEL.PIPELINE_HEALTH_FEATURES`.

`OPSINTEL.PIPELINE_DEPENDENCY_CASCADE` uses Exasol's hierarchical `CONNECT BY`
processing to traverse dependencies. The API retains failed downstream runs
only when their latest failure occurs after the upstream failure and within a
120-minute window, and returns both timestamps plus correlation lag. This is
temporal correlation, not confirmed causation. The dashboard reads the result
from `/analytics/cascades`.

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

## Controlled comparative benchmark

`reports/database-comparison.json` records the same deterministic workload on
Exasol Personal and DuckDB at one million and ten million rows, sequentially on
the same machine, with seven measured queries per engine. Exasol's query cache
was disabled so repeated result retrieval was not presented as SQL execution.

| Rows | Exasol median | DuckDB median | Faster in this run |
|---:|---:|---:|---|
| 1,000,000 | 437.118 ms | 114.912 ms | DuckDB |
| 10,000,000 | 4,902.269 ms | 1,080.358 ms | DuckDB, about 4.5× |

This local single-user result does not establish concurrency, distributed
scale, cost, or production performance. It also does not support an Exasol
speed-win claim. Exasol's demonstrated role is the shared operational evidence
layer: window analytics, live evidence retrieval, and a hierarchical
`CONNECT BY` cascade consumed by the API and dashboard.

## Limitations

- The scenarios and logs are synthetic.
- The public-message corpus contains nine short licensed framework messages,
  not representative production log streams; its labels are project-authored.
- The regression and project-authored holdout sets are small and are stored with the
  implementation.
- External-reviewer holdout status: **0 cases recorded by 0 external authors**.
  The project team authored the published 27-case versioned holdout.
- Keyword rules do not establish semantic understanding.
- The optional LLM boundary has 14/14 passing mocked tests, but no live or
  independent quality evaluation has been performed.
- Human-impact study status: **0/40 assigned trials recorded across 0/4
  participants**. The repository includes ten frozen cases, a counterbalanced
  assignment, a blank measurement template, and a deterministic result
  summarizer that withholds comparison metrics until the full balanced baseline
  is present. No time-saving or causal-impact result is claimed.
- Candidate explanations remain unconfirmed until an engineer verifies them.
- Concurrency and production infrastructure have not been evaluated. Airflow
  and dbt exported-JSON adapter samples are included, but they are not live
  orchestrator connectors.
