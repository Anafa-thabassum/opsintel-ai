# Judge Q&A

## Why does this need Exasol?

Exasol stores the operational history and computes the features consumed by the
dashboard. The analytical view uses window functions for previous-run status,
rolling row-count baselines, completeness, and rolling failure rate. Moving
those calculations into the database keeps the API thin and makes the evidence
queryable and reproducible.

## Is this really AI?

The current prototype uses a transparent rule-based classifier. “AI-assisted”
describes the investigation workflow, not a claim that an LLM is integrated.
This was deliberate: a hackathon prototype should expose why it suggested a
candidate and should abstain when evidence is insufficient.

## How do you prevent hallucinations?

The system separates observations, candidates, and confirmation. Evidence is
quoted from Exasol records, candidate causes are labelled as unconfirmed, and
the confirmed root cause remains null. Unknown evidence is allowed to remain
unclassified.

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

## Why not add an LLM now?

An LLM would add novelty but not evidence. The current version proves the core
workflow and safety boundary first. A future model could summarize long logs or
rank candidates, but it should remain grounded in retrieved records and should
not bypass confirmation.
