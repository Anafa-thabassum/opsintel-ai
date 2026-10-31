# Verified Incident Memory

## Contract

`POST /memory/submissions` records an investigator's hypothesis as `pending`; it does not confirm a cause. An explicitly authorized, different reviewer can approve, reject, or request more evidence through `POST /memory/submissions/{id}/review`. Approval requires the versioned checklist, evidence references for every criterion, symptom support, cause-specific evidence, and no unresolved conflict. The reviewer decision is recorded with identity, rationale, timestamp, packet, checklist, and an audit snapshot.

Approved records are in `OPSINTEL.CONFIRMED_INCIDENTS`; submissions, features, matches, and decisions are stored in `INCIDENT_SUBMISSIONS`, `INCIDENT_FEATURES`, `INCIDENT_MATCHES`, and `INCIDENT_AUDIT`. Corrections and revocations preserve the old state in audit and mark affected matches stale. Revoked incidents are excluded from retrieval. Exasol enforces one current confirmation per run ID.

These are approved design and workflow policies, not empirically validated causal criteria. A reviewer cannot override missing/contradictory evidence. No automatic repair occurs.

## Authorization and evidence

The backend reads `OPSINTEL_AUTH_TOKENS_JSON`, a map of random bearer tokens to `actor_id` and `role` (`investigator` or `reviewer`). Memory endpoints return 503 when grants are absent, 401 for an invalid token, and 403 for insufficient role. The submitter cannot approve their own submission. Do not store credentials in Vite variables or source control.

Evidence items carry a `reference`, exact `excerpt`, `kind` (`symptom` or `causal`), and optionally `source_uri`/`observed_at`. In-run references must match actual investigation evidence. External references must be HTTPS and are not fetched or authenticated by the server; the human reviewer must inspect the source. Similarity scores are retrieval scores, not causal probabilities.

## Retrieval behavior

`GET /memory/similar/{run_id}` filters active historical memories and excludes the query run in Exasol, loads up to 500 recent records, fingerprints and compares in Python, and returns up to three candidates. It does not mutate the current incident to confirmed. No qualifying candidate returns `unresolved` memory status.

## Live evidence status

The local Exasol demonstration used temporary test identities and source excerpts from Airflow issue #36734. The approval was revoked after the demonstration. This verified SQL/API persistence and transition behavior; it is not a real human review or human-impact study. There are currently no active human-reviewed memory records, so increasing-history performance remains unmeasured. See [runtime report](../reports/exasol-memory-e2e-2026-10-31.md), [benchmark protocol](../reports/exasol-memory-benchmark-protocol-v1.md), and the [browser rehearsal checklist](verified-incident-memory-browser-rehearsal.md).
