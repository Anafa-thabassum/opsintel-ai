# Exasol integration

OpsIntel uses Exasol for operational analysis and verified memory storage. It does not claim that Jaccard matching runs inside Exasol.

| Operation | Location | SQL or code |
|---|---|---|
| Incident detection, completeness, previous status, rolling average and failure rate | Exasol analytical view | `sql/analysis/pipeline_health_features.sql` |
| Dependency paths | Exasol `CONNECT BY` view | `sql/analysis/pipeline_dependency_cascade.sql` |
| Failed run comparison and source log retrieval | Exasol queries | `app/investigator.py` |
| Active memory candidate filtering, source-run exclusion, operational counts | Exasol queries | `app/memory.py` |
| Verified records, features, matches, submissions, audit | Exasol tables | `sql/migrations/001_verified_incident_memory.sql` |
| Log normalization, token pairs, Jaccard, contradiction penalties | Application | `app/fingerprint.py` |
| Public issue storage, filtered search, source/category aggregation | Exasol table and grouped SQL | `sql/migrations/002_public_incidents.sql`, `app/public_data.py` |
| Public issue extraction, PII screening and text-neighbour scoring | Application | `app/public_data.py` |

Initialize a **disposable** Exasol Personal instance using `python -m scripts.setup_database --reset` only when resetting it is explicitly safe. For an existing OPSINTEL schema, use `python -m scripts.setup_database` without `--reset`. Then run `python -m scripts.migrate_database` to inspect pending migrations and `python -m scripts.migrate_database --apply` to add verified memory. The migration is additive and records its SHA-256 in `OPSINTEL.SCHEMA_MIGRATIONS`; editing an applied migration is rejected.

The local Exasol Personal deployment was started without resetting data. The additive migration applied successfully, its SHA-256 was recorded in `SCHEMA_MIGRATIONS`, and the existing five telemetry tables retained their row counts. A rollback-only rehearsal exercised submission, reviewer-decision SQL, retrieval, candidate rejection, revocation, and audit reads; all five memory data tables remained empty afterward. This verifies SQL compatibility and transaction behavior, **not** real human confirmation, causal accuracy, sustained performance, or a clean-environment deployment. Those validations remain pending.

Migration `002_public_incidents.sql` was also applied locally. Ten official
GitHub issue records were fetched into `OPSINTEL.PUBLIC_INCIDENTS`; live
filtered reads, pagination and grouped counts succeeded. `make public-ingest`
re-fetches the registered issues and updates a row only when its body, update
timestamp, excerpt or classifier category changes. Search and aggregations
execute in Exasol; the deterministic classifier and textual similarity execute
in Python. This small collection is not a performance benchmark.
