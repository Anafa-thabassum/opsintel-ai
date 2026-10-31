# Installation

## Supported local environment

The GitHub Actions workflow uses Python 3.12 and Node.js 20. The checked-in Vite package requires Node `^20.19.0 || >=22.12.0`. The latest recorded local development environment uses Python 3.14, Node 26.11.1, and npm 11.20.0. Requirements are pinned in `requirements.txt`; frontend dependencies are locked in `frontend/package-lock.json`.

## Clone and install

```bash
git clone https://github.com/Anafa-thabassum/opsintel-ai.git
cd opsintel-ai
make setup
```

`make setup` creates `.venv`, installs `requirements.txt`, and runs `npm ci` in `frontend/`. To install manually:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
cd frontend && npm ci
```

## Exasol

Install and start Exasol Personal separately. The default app DSN is `127.0.0.1:8563`; credentials come from `EXASOL_PASSWORD` or Exasol Personal's default `~/.exasol/personal/deployments/default/secrets.json`. Configure other endpoints as described in [Configuration](CONFIGURATION.md). Remote DSNs require `EXASOL_TLS_VERIFY=true`.

For a new synthetic demo schema, run `make database`. For an existing `OPSINTEL` schema, this setup script preserves existing tables and data and refreshes its analytical views. Then inspect and apply additive migrations as needed:

```bash
make memory-check
make memory-migrate
```

`make memory-check` reports pending migrations without applying them; `make memory-migrate` applies them. Do not reset or drop a schema containing memory or public issue tables.

## Start services

Backend from the repository root:

```bash
set -a; source .env; set +a
make api
```

Frontend in another terminal:

```bash
cd frontend
cp .env.example .env
npm ci
npm run dev
```

`VITE_API_URL` is read at frontend build/dev time. See [Quickstart](QUICKSTART.md) for a complete sequence and [Exasol setup](EXASOL_SETUP.md) for schema details.
