# Verified Incident Memory

## State and contract

`POST /memory/submissions` records an investigator's causal hypothesis as **pending**, with an evidence packet and fingerprint. It does not change `confirmed_root_cause`. A different explicitly authorized reviewer uses `POST /memory/submissions/{id}/review` to approve, reject, or request more evidence. Approval requires the versioned class checklist, traceable evidence for every criterion, a separately marked causal source for mechanism checks, and no unresolved classifier conflict. These are design gates; they have **not been empirically validated** as proof of real-world causal accuracy.

An approved record is stored in `OPSINTEL.CONFIRMED_INCIDENTS` and its observed features in `OPSINTEL.INCIDENT_FEATURES`. Decisions and prior state snapshots are append-only in `OPSINTEL.INCIDENT_AUDIT`. `OPSINTEL.INCIDENT_SUBMISSIONS` stores the full submitted and reviewed packet. `OPSINTEL.INCIDENT_MATCHES` records candidate/rejected/stale retrieval decisions. An active record can be corrected through a new submission or revoked by a reviewer. A correction preserves the original incident ID, increments its revision, writes the previous state to audit, and stales old matches. Revoked records are excluded from matching.

Exasol enforces a unique run ID for current confirmations through the `RUN_ID` primary key. Application checks also reject duplicates. A pending submission does not reserve a run; a concurrent approval is checked again inside the transaction, and the primary key is the final guard. Never reset the schema to apply memory migrations.

## Authorization

Set `OPSINTEL_AUTH_TOKENS_JSON` through a secret manager as a JSON object mapping long random bearer tokens to `{"actor_id":"...","role":"investigator"}` or `{"actor_id":"...","role":"reviewer"}`. No grants means memory endpoints return 503. Read and write memory endpoints require a valid token. Only reviewer grants can approve and revoke. The submitter and reviewer actor IDs must differ. The browser holds the entered token only in page memory. The email demo gate is not authentication.

This token mechanism is appropriate for a controlled hackathon deployment with a trusted TLS gateway. It lacks account management, token rotation, rate limiting, and enterprise identity integration; a public deployment needs those controls. Never put a token in `VITE_*` variables or source control.

## Evidence and verification

An incident reference must match an actual observation returned for the investigated run, including the exact excerpt. An additional source may use an HTTPS URL and a nonempty excerpt. The server does not fetch or authenticate arbitrary external pages; the reviewer must inspect them. A submission needs distinct symptom and causal source references; the symptom sources alone must support the proposed category. The submitted original and additional evidence is also reclassified, and approval requires no conflict. Every packet item is marked `symptom` or `causal`. Cause-specific mechanism and causal-link checks require a causal source reference. The five required checks for each class are the three class criteria in `app/memory.py` and `alternatives_reviewed` plus `contradictions_resolved`. The detailed approved class policies are in `reports/classifier-design-addendum-v1.md`. Human approval cannot override a missing check or active conflict.

For a demonstration, use a disposable Exasol Personal database, run the additive migration, and configure distinct investigator and reviewer grants. Submit a hypothesis only when actual source records support its mechanism. If the sample run lacks causal evidence, the correct outcome is pending or needs more evidence. Do not invent a confirming source to make a demo pass.

## Retrieval

`GET /memory/similar/{run_id}` filters active records and excludes the same run in Exasol, then compares at most 500 candidates in the application. It returns up to three matches above the documented threshold, with matching/differing features and a label requiring engineer verification. A rejected match is not shown again unless the historical confirmation is corrected. If nothing qualifies, memory status is `unresolved`; the incident's symptom classification is unaffected. See [fingerprinting](incident-fingerprinting.md).
