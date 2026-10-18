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
export EXASOL_USER="sys"
export EXASOL_PASSWORD="your-password"
export EXASOL_TLS_VERIFY="true"
export CORS_ORIGINS="https://your-dashboard.example"
python -m scripts.setup_database
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Place the API behind an HTTPS reverse proxy and restrict network access to the
Exasol endpoint. The development default disables certificate verification for
local Exasol Personal only.

### Frontend

`VITE_API_URL` is embedded at build time:

```bash
cd frontend
npm ci
VITE_API_URL="https://your-api.example" npm run build
```

Serve `frontend/dist/` from any static host. Verify `/health`, `/incidents`,
`/analytics/trend`, and one `/investigate/{run_id}` request before sharing the
deployment.

## Production gap

The prototype does not include authentication, authorization, orchestrator
connectors, multi-user concurrency validation, or audited data retention. Add
those controls before using real operational data.
