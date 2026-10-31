# API reference

FastAPI's generated OpenAPI and request models are available at `/docs` while the backend runs. All endpoints use JSON except the interactive API page.

## Investigation and analytics

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Service name/status |
| GET | `/health` | Database connection check |
| GET | `/incidents` | Failed/incomplete pipeline runs |
| GET | `/analytics/trend` | Exasol daily run/incident metrics |
| GET | `/analytics/cascades` | Time-bounded dependency-path correlations |
| GET | `/investigate/{run_id}` | Evidence, comparison, symptom assessment, candidates, optional narrative |
| GET | `/investigate/{run_id}/root-causes` | Deterministic candidate assessment |
| GET | `/scorecard/public` | Read-only public failure-corpus scorecard |

## Public issue mode

| Method | Path | Purpose |
|---|---|---|
| GET | `/public/sources` | Registry, repository license, issue-text status |
| GET | `/public/incidents` | Search/filter/page cached records |
| GET | `/public/incidents/{owner}/{repo}/{number}` | One issue record and provenance |
| GET | `/public/similar/{owner}/{repo}/{number}` | Text-similar public records; not causal candidates |
| GET | `/public/analytics` | Exasol source/category aggregates |
| GET | `/public/evaluation` | Project-label comparison; not independent accuracy |

Ingest first with `make public-ingest`; these routes do not fetch new issues on each request. Except `/public/sources`, public-data routes require Exasol.

## Verified Incident Memory

All memory routes require `Authorization: Bearer <configured-token>`.

| Method | Path | Role / purpose |
|---|---|---|
| GET | `/memory/criteria/{category}` | Authenticated; reviewer checklist definitions |
| GET | `/memory/incidents` | Authenticated; current and revoked records |
| GET | `/memory/incidents/{run_id}` | Authenticated; memory for a run |
| GET | `/memory/analytics` | Authenticated; operational counts, not accuracy |
| GET | `/memory/history/{run_id}` | Authenticated; audit history |
| GET | `/memory/submissions` | Investigator's submissions or reviewer queue |
| POST | `/memory/submissions` | Investigator; create a hypothesis submission |
| POST | `/memory/submissions/{submission_id}/review` | Reviewer; approve/reject/request more evidence |
| POST | `/memory/incidents/{incident_id}/revoke` | Reviewer; revoke an active record with rationale |
| GET | `/memory/similar/{run_id}` | Authenticated; candidate retrieval |
| POST | `/memory/matches/{match_id}/reject` | Investigator/reviewer; reject a candidate |

Submission payload fields include `run_id`, `category`, `cause_description`, `evidence[]`, `kind` (`new`/`correction`), and `source_incident_id` for corrections. Evidence has `reference`, `excerpt`, `kind`, and optional `source_uri`, `observed_at`. Review payload has `decision`, `rationale`, and a versioned `checklist` with criteria and evidence references. Revocation needs a rationale. See the OpenAPI schema for exact constraints.

Expected failures include 401 invalid token, 403 wrong role, 404 unknown record, 409 conflicting/stale state, 422 invalid payload, and 503 unavailable database or missing memory authorization configuration. Middleware adds `X-Request-ID` and `X-Response-Time-Ms`; logs do not include request bodies or evidence excerpts.
