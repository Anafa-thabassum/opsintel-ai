# Exasol setup

## Start and connect

Install Exasol Personal and start it from the Personal application. If its CLI is installed:

```bash
exasol start --wait-timeout-minutes 3
```

The local defaults in `app/db.py` are `EXASOL_DSN=127.0.0.1:8563`, user `sys`, and TLS verification off for loopback. If `EXASOL_PASSWORD` is unset, the app reads `~/.exasol/personal/deployments/default/secrets.json`. Never use the demo `sys` account for remote deployment. Remote DSNs require `EXASOL_TLS_VERIFY=true`.

Check the database connection and API:

```bash
make memory-check
curl http://127.0.0.1:8000/health
```

`/health` executes `SELECT 1 FROM DUAL`. It does not initialize the schema.

## Initialize and migrate

On a new demo database:

```bash
make database
make memory-check
make memory-migrate
```

`make database` creates the synthetic `OPSINTEL` schema and seeds it only if the schema does not already exist; it then creates/replaces analytical views. `make memory-check` lists pending additive migrations without applying them. `make memory-migrate` applies migrations and stores each migration file's SHA-256 in `OPSINTEL.SCHEMA_MIGRATIONS`.

- `sql/schema.sql` and `sql/seed.sql`: synthetic run/log/dependency demonstration tables.
- `sql/analysis/pipeline_health_features.sql`: completeness, incident flags, `LAG` prior status, and rolling window calculations.
- `sql/analysis/pipeline_dependency_cascade.sql`: hierarchical dependency paths through `CONNECT BY`.
- `sql/migrations/001_verified_incident_memory.sql`: submissions, confirmed incidents, features, matches, and audit tables.
- `sql/migrations/002_public_incidents.sql`: the separate cached public issue table.

Never edit an applied migration. Add a new numbered migration instead. Migrations are additive and do not seed, reset, or delete telemetry.

## Safety for existing data

`make database-reset` drops the full `OPSINTEL` schema. The setup script refuses when it finds verified-memory or public-issue tables, but that guard is not a backup. Use reset/smoke commands only with a database confirmed disposable and explicitly authorized. Never remove Exasol volumes to troubleshoot a refused connection.

For an existing schema, prefer:

```bash
make database       # preserves existing tables/data and ensures views
make memory-check   # inspect pending migrations
make memory-migrate # apply additive changes if intended
```

## Exasol's analytical role

Exasol calculates run-health windows, daily summaries, and dependency traversal and serves current run/log evidence to the API. It stores durable memory and public-issue records. The application computes token-pair fingerprints and similarity scores. See the measured local database comparisons in [reproducibility and evaluation](../reports/reproducibility-and-evaluation.md); those synthetic single-user runs showed DuckDB faster on this machine and are not production comparisons.
