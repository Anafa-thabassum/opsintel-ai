# Judge Q&A

## Why does this need Exasol?

Exasol stores the operational history and computes the features consumed by the
dashboard. The analytical view uses window functions for previous-run status,
rolling row-count baselines, completeness, and rolling failure rate. Moving
those calculations into the database keeps the API thin and makes the evidence
queryable and reproducible. A second Exasol view uses hierarchical `CONNECT BY`
processing to correlate one failed upstream pipeline with three failed
downstream runs. The benchmark loader uses PyExasol's bulk iterable import path;
the project does not claim to implement a UDF.

The controlled cache-off comparison did not show an Exasol speed advantage:
DuckDB was about 4.5× faster at 10M rows on this laptop. Exasol earns its role
here by keeping shared operational evidence and cross-pipeline analysis in the
database used by the live API, not by an unsupported benchmark claim.

The cascade is temporal correlation, not confirmed causation. The API retains
only downstream failures that occur after the upstream failure and within 120
minutes, and reports the timestamps and lag for judge inspection.

## Is this really AI?

The core classifier and candidate generation are transparent, deterministic
rules. An optional LLM then summarizes only the retrieved evidence and lists
evidence gaps. The model does not create the source observations, confirm a
root cause, or execute a repair.

## How do you prevent hallucinations?

The system separates observations, candidates, the optional narrative, and
human confirmation. The model receives a bounded JSON payload, treats record
content as untrusted data, and returns a strict claim schema. The confirmed
root cause remains null even when the summary is generated. Every generated
claim must cite one or more retrieved evidence IDs or the whole response is
discarded. Each reference also needs an exact excerpt from its cited
observation. Facts are checked only against the cited observations, and
evidence gaps must match server-owned options for the deterministic category.
Post-response checks reject new numeric facts, run/log IDs, confirmed-cause
language, and repair claims. Unknown evidence
can remain unclassified, and model failure leaves the deterministic result
available.

## What happens when the rules are wrong?

The recommendation is a diagnostic starting point, not an automated repair.
The engineer can inspect every source observation. Regression cases include
paraphrases and benign timeout configuration. A separate 27-case versioned
synthetic holdout scored 27/27 across all nine outcomes. Its dataset and result
entered Git history together, so it does not independently prove freeze order.
An external evaluator must use the reviewer template, which currently contains
0 cases from 0 external authors.

## What has been measured?

One hundred thirty-seven automated tests, a predefined 16-case synthetic
regression set, a separate 27-case versioned project-authored holdout, frontend
quality checks, and a
reproducible local Exasol scale benchmark. The holdout is project-authored. The
external holdout has 0 cases from 0 authors, while the frozen four-participant
impact study has 0/40 recorded trials from 0/4 participants.

A separate licensed public-message corpus covers nine short messages from
Apache Spark, Apache Airflow, and dbt-common. It scores 6/9 with every source,
licence, prediction, and mismatch published. Its labels are project-authored,
so it measures vocabulary compatibility rather than independent accuracy.

## How does the system handle an unseen failure?

It does not force the closest known label. If no deterministic rule has
traceable support, the result is `unclassified`, the confirmed root cause stays
unset, and the dashboard asks for the missing logs or metrics. The regression
and project-authored holdout sets include unknown log patterns, but an
independent external holdout remains pending.

## What happens when the evidence conflicts?

Success and failure signals in the same incident produce
`conflicting_evidence`. The system recommends checking the final orchestrator
state and latest log record rather than choosing one signal or confirming a
cause.

## Does the browser demo gate protect the API?

No. The gate is presentation-only session state. Every API endpoint is served
independently by FastAPI and must be protected by real authentication and
authorization before production use.

## How does this scale?

The repository demonstrates a sequential local 1M/10M analytical workload and
does not claim concurrent or production throughput. Production validation
would need representative concurrency, workload isolation, connection-pool
limits, retention sizing, and monitored service-level objectives.

## How do you know it works?

The evidence is layered: automated tests verify software behavior, the 16-case
suite verifies predefined classifier regressions, the 27-case project-authored
holdout exercises all outcomes, and recorded database benchmarks verify the
documented SQL workload. None of those substitutes for external-reviewer cases
or participant impact measurements, which remain explicitly at zero.

## What would productionization require?

Authentication and authorization, orchestrator connectors, production data
contracts, audited retention, monitored classification quality, an external
holdout evaluation, a human impact study, and deployment-specific TLS and
secret management.

## What does the LLM add?

It makes a multi-record investigation easier to read by producing a concise
narrative whose individual claims link to retrieved evidence, and identifies
missing evidence. It does not add evidence, change
the deterministic category, rank candidates, or bypass human confirmation.
The integration is optional and disabled by default.
