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
discarded. Unknown evidence
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

One hundred fifteen automated tests, a predefined 16-case synthetic regression set, a separate
27-case versioned project-authored holdout, frontend quality checks, and a
reproducible local Exasol scale benchmark. The holdout is project-authored. The
external holdout has 0 cases from 0 authors, while the frozen four-participant
impact study has 0/40 recorded trials from 0/4 participants.

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
