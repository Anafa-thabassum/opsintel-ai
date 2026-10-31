# Data flow

## Synthetic pipeline investigation

1. `sql/schema.sql` and `sql/seed.sql` define and populate the synthetic `OPSINTEL.PIPELINE_RUNS`, `PIPELINE_LOGS`, and dependency tables on a new demo schema.
2. Exasol views calculate incident flags, missing/excess rows, completeness, prior status, rolling row baselines, and rolling failure rates.
3. `GET /incidents` selects failed or incomplete runs. `GET /investigate/{run_id}` retrieves run metadata, relevant logs, and the latest successful comparison.
4. The deterministic classifier normalizes evidence fields, extracts structured signals, evaluates text cues, negation and contradictions, and returns symptom categories with evidence references or an unresolved outcome.
5. Candidate assessment explains possible causes and missing evidence. It does not promote them to `confirmed_root_cause`.
6. If enabled, the LLM receives the selected evidence and candidate facts to create a narrative. The integration checks returned claims against cited excerpts; failure leaves the deterministic result available.
7. React renders observations, evidence, candidates, uncertainty, and safe next diagnostic actions.

## Public issue mode

The pinned registry identifies public GitHub issues. `scripts/ingest_public_issues.py` fetches issue metadata and text, screens excerpts, records source URL, timestamps, body hash, source origin, and license status, and writes the separate `OPSINTEL.PUBLIC_INCIDENTS` table. Search and aggregation use Exasol; deterministic classification and text-neighbour scoring run in Python. Project labels remain distinguishable from external source evidence. Issue text licensing is not inferred from the code repository license.

## Verified Incident Memory

An investigator submits an evidence-backed hypothesis. A different authorized reviewer sees the packet and versioned checklist. Passing review stores a confirmed record, features, and an append-only audit event. Retrieval filters active records in Exasol, excludes the same run, scores at most 500 candidates in Python, and returns at most three citations. Corrections and revocations are reviewed transitions; they retain history and mark prior matches stale. Retrieval never confirms the current incident.

See [API reference](API_REFERENCE.md) for routes and [Exasol setup](EXASOL_SETUP.md) for tables/views.
