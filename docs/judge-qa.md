# Judge Q&A

## Why does this need Exasol?

Exasol stores the operational history and computes the features consumed by the
dashboard. The analytical view uses window functions for previous-run status,
rolling row-count baselines, completeness, and rolling failure rate. Moving
those calculations into the database keeps the API thin and makes the evidence
queryable and reproducible.

## Is this really AI?

The core classifier and candidate generation are transparent, deterministic
rules. An optional LLM then summarizes only the retrieved evidence and lists
evidence gaps. The model does not create the source observations, confirm a
root cause, or execute a repair.

## How do you prevent hallucinations?

The system separates observations, candidates, the optional narrative, and
human confirmation. The model receives a bounded JSON payload, treats record
content as untrusted data, and returns a strict summary schema. The confirmed
root cause remains null even when the summary is generated. Unknown evidence
can remain unclassified, and model failure leaves the deterministic result
available.

## What happens when the rules are wrong?

The recommendation is a diagnostic starting point, not an automated repair.
The engineer can inspect every source observation. Regression cases include
paraphrases and benign timeout configuration, while the independent holdout
runner lets an external evaluator measure unseen cases against a frozen commit.

## What has been measured?

Automated tests, a predefined 16-case synthetic regression set, frontend
quality checks, and a reproducible local Exasol scale benchmark. These are not
presented as production accuracy or a human productivity study.

## What would productionization require?

Authentication and authorization, orchestrator connectors, production data
contracts, audited retention, monitored classification quality, an external
holdout evaluation, a human impact study, and deployment-specific TLS and
secret management.

## What does the LLM add?

It makes a multi-record investigation easier to read by producing a concise
narrative and identifying missing evidence. It does not add evidence, change
the deterministic category, rank candidates, or bypass human confirmation.
The integration is optional and disabled by default.
