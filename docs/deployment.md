# Deployment guide

## Demo deployment

The reference deployment uses Exasol Personal, FastAPI, and a static React
build. Keep Exasol credentials only in the backend environment.

### Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
export EXASOL_DSN="your-exasol-host:8563"
export EXASOL_USER="opsintel_app"
export EXASOL_PASSWORD="your-password"
export EXASOL_TLS_VERIFY="true"
export CORS_ORIGINS="https://your-dashboard.example"
# Optional evidence-grounded narrative summary:
export OPSINTEL_LLM_ENABLED="true"
export OPENAI_API_KEY="your-openai-api-key"
export OPSINTEL_LLM_MODEL="gpt-6-luna"
python -m scripts.setup_database
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Place the API behind an HTTPS reverse proxy and restrict network access to the
Exasol endpoint. The development default disables certificate verification for
local Exasol Personal only; a non-loopback `EXASOL_DSN` is rejected unless
`EXASOL_TLS_VERIFY=true`. The `sys` account in `.env.example` is solely for the
local synthetic demonstration. Use a dedicated, least-privileged application
identity for a remote deployment. Keep `OPENAI_API_KEY` in the backend secret store,
allow outbound HTTPS access to `api.openai.com`, and review operational log
content before sending it to an external model. Leave `OPSINTEL_LLM_ENABLED`
unset or `false` for deterministic-only deployments.

### Frontend

`VITE_API_URL` is embedded at build time:

```bash
cd frontend
npm ci
VITE_API_URL="https://your-api.example" npm run build
```

Serve `frontend/dist/` from any static host. Verify `/health`, `/incidents`,
`/analytics/trend`, `/analytics/cascades`, and one `/investigate/{run_id}`
request before sharing the deployment.

For a local end-to-end database/API rehearsal against a confirmed disposable
Exasol deployment, run the smoke check once from the repository root:

```bash
make smoke
```

`make smoke` already invokes the `database` target, which resets the synthetic
`OPSINTEL` schema. Do not run it against an existing or unconfirmed database.
The smoke check verifies database health, seeded incidents, a failed-run versus
last-success comparison, the safe unconfirmed state, and the dependency cascade.

The frontend demo-access screen is a presentation boundary only. It stores a
temporary flag in browser session storage and must not be treated as an
authentication or authorization control.

## Production gap

The prototype does not include production authentication, authorization, live
orchestrator connections, multi-user concurrency validation, audited data
retention, or an independent evaluation of LLM summary quality. Exported JSON
adapter examples for Airflow and dbt are documented under
`examples/integrations/`. Add production controls before using real operational
data. The configured model identifier is documented, but account entitlement
and live grounding remain unverified because no authorized live request has
been recorded.

## Local verification shortcut

From the repository root, `make setup` installs Python and frontend
dependencies, and `make verify` runs the complete automated verification. The
Exasol service must already be reachable before `make database`, `make smoke`,
or `make benchmark` is used. `make verify` does not reset or require Exasol.
