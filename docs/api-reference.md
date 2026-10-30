# API reference

All existing `GET /health`, `/incidents`, `/analytics/trend`, `/analytics/cascades`, `/investigate/{run_id}`, `/investigate/{run_id}/root-causes`, and `/scorecard/public` contracts remain available. Investigation responses retain their legacy fields and canonical classification/evidence assessments.

Public issue mode is read-only. It queries the locally populated Exasol
`OPSINTEL.PUBLIC_INCIDENTS` table and never treats a public issue as a verified
cause. Ingest records with `python -m scripts.ingest_public_issues` first.

| Method | Path | Purpose |
|---|---|---|
| GET | `/public/sources` | Registry, code licence and issue-text terms status |
| GET | `/public/incidents` | Search and paginate; `source`, `category`, `search`, `limit`, `offset` |
| GET | `/public/incidents/{owner}/{repo}/{number}` | One cached issue and its source evidence |
| GET | `/public/similar/{owner}/{repo}/{number}` | Up to three unverified text neighbours |
| GET | `/public/analytics` | Exasol grouped source/category counts |
| GET | `/public/evaluation` | Current project-label comparison; no independent accuracy claim |

Public data endpoints return 503 when Exasol is unavailable; `/public/sources`
reads the versioned local registry and does not require a database. Similarity
scores measure text overlap, not causal probability. See
[public data ingestion](public-data-ingestion.md).

Verified memory endpoints require `Authorization: Bearer <configured-token>`. An investigator grant can submit hypotheses and reject matches. A reviewer grant can also approve/reject submissions and revoke confirmations. A reviewer cannot approve a submission with the same actor ID.

| Method | Path | Purpose |
|---|---|---|
| GET | `/memory/criteria/{category}` | Versioned reviewer checklist IDs |
| GET | `/memory/incidents` | Current confirmed records, including revoked records |
| GET | `/memory/incidents/{run_id}` | Current record for one run |
| GET | `/memory/analytics` | Exasol operational counts, not accuracy |
| GET | `/memory/history/{run_id}` | Append-only decision history |
| GET | `/memory/submissions` | Recent reviewer queue |
| POST | `/memory/submissions` | Submit new or correction hypothesis |
| POST | `/memory/submissions/{id}/review` | Reviewer decision |
| POST | `/memory/incidents/{id}/revoke` | Reviewer revocation with rationale |
| GET | `/memory/similar/{run_id}` | Up to three historical candidates or unresolved memory result |
| POST | `/memory/matches/{id}/reject` | Reject a retrieval candidate for this run |

Submission JSON contains `run_id`, one supported `category`, `cause_description`, `evidence[]`, `kind` (`new` or `correction`), and `source_incident_id` for corrections. Each evidence item has `reference`, exact `excerpt`, and `kind` (`symptom` or `causal`); external sources also need a matching HTTPS `source_uri`. Distinct symptom and causal references are required, and symptom references must support the category on their own. A review contains `decision`, `rationale`, and a checklist with `version`, all required `criteria[]` (`id`, `passed`, `method`, `result`, `evidence_refs`), and `unresolved_conflicts`. A revocation contains `rationale`.

Typical errors: 401 missing/invalid token, 403 wrong role, 404 missing record, 409 duplicate or stale state, 422 invalid evidence/checklist, 503 unavailable database or authorization configuration. Database details and credentials are not returned in API errors. OpenAPI at `/docs` shows the exact request models.

Every response includes `X-Request-ID` and `X-Response-Time-Ms`. Server logs record the route template, status, and latency without request bodies, bearer tokens, or source excerpts. Exasol connections have bounded connection, socket, and query timeouts.
