# Quickstart

This starts the synthetic demo against Exasol Personal. It does not reset an existing schema.

## Requirements

- Exasol Personal installed and running. Default DSN: `127.0.0.1:8563`.
- Python 3.12+ (CI uses 3.12; local development has used 3.14).
- Node.js 20.19+ or 22.12+ and npm.

## Start the project

```bash
git clone https://github.com/Anafa-thabassum/opsintel-ai.git
cd opsintel-ai
make setup
exasol start --wait-timeout-minutes 3   # if the Exasol Personal CLI is installed
cp .env.example .env
set -a; source .env; set +a
make database
make memory-migrate
make api
```

In another terminal:

```bash
cd opsintel-ai/frontend
cp .env.example .env
npm ci
npm run dev
```

Open <http://127.0.0.1:5173>. Check the API and inspect a seeded run:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/investigate/1
```

The backend does not automatically load `.env`; export the variables into its process as above. The memory endpoints stay disabled until `OPSINTEL_AUTH_TOKENS_JSON` is configured. See [Configuration](CONFIGURATION.md) and [Verified Incident Memory](VERIFIED_INCIDENT_MEMORY.md).

## Verify

```bash
make verify
```

This runs Python tests, a 16-case synthetic classifier challenge, frontend lint, and a production build. It does not need Exasol or reset data. For evidence boundaries and separate evaluation sets, see [Evaluation methodology](evaluation-methodology.md) and the [reproducibility report](../reports/reproducibility-and-evaluation.md).

Do not use `make database-reset` or `make smoke` against any database that is not confirmed disposable. Those targets reset synthetic `OPSINTEL` data.
