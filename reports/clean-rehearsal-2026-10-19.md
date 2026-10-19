# Batch 6 clean-clone rehearsal

Date: 19 October 2026 (Asia/Kolkata)

This is a new rehearsal record. The earlier `reports/clean-rehearsal.md` remains
unchanged as historical evidence.

## Candidate and environment

| Item | Value |
|---|---|
| Tested revision | `2a17d4fa92af2699a9acb1a0d5b261bf3776b808` |
| Source preparation | Local `git clone --no-local`; no working-tree files copied |
| Rehearsal directory | `/private/tmp/opsintel-rehearsal-keGK5x/opsintel-ai` |
| Operating system | macOS 26.6.2, build 25G83, arm64 |
| Python | 3.14.0 |
| pip | 25.2 in the new virtual environment |
| Node.js | 26.11.1 |
| npm | 11.20.0 |
| Git | 2.51.1 |

The clone initially contained no `.venv`, `node_modules`, `frontend/dist`, or
`.env`. No local secret file or credential was copied. The optional LLM was
disabled. Database checks used an intentionally unreachable loopback port and
the non-secret placeholder password `rehearsal-placeholder`.

## Commands and outcomes

| Step | Exact command | Outcome |
|---|---|---|
| Fresh source | `git clone --no-local /Users/anafathabassumsadiq/opsintel-ai /private/tmp/opsintel-rehearsal-keGK5x/opsintel-ai` | Passed |
| Revision | `git rev-parse HEAD` | `2a17d4fa92af2699a9acb1a0d5b261bf3776b808` |
| Dependency setup | `make setup` | Passed after network access was allowed |
| Automated verification | `make verify` | Passed |
| API start | `EXASOL_DSN=127.0.0.1:65534 EXASOL_USER=sys EXASOL_PASSWORD=rehearsal-placeholder EXASOL_TLS_VERIFY=false OPSINTEL_LLM_ENABLED=false .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 18000` | Started successfully |
| API identity | `curl http://127.0.0.1:18000/` | HTTP 200 |
| OpenAPI | `curl http://127.0.0.1:18000/openapi.json` | HTTP 200 |
| Database health | `curl http://127.0.0.1:18000/health` | HTTP 503, expected because the disposable DSN was intentionally unreachable |
| Frontend start | `VITE_API_URL=http://127.0.0.1:18000 npm run dev -- --host 127.0.0.1 --port 15173` | Started successfully |
| Frontend HTTP | `curl http://127.0.0.1:15173/` | HTTP 200; title `OpsIntel AI` |

The first sandboxed `make setup` attempt could not resolve the Python package
index and failed with `No matching distribution found for fastapi==0.143.1`.
That was an environment network restriction, not a dependency mismatch. The
same documented command succeeded after network access was explicitly allowed.

## Verification results

| Check | Result |
|---|---:|
| Python dependency installation | Passed |
| Frontend dependency installation | Passed; npm reported 0 vulnerabilities |
| Python tests | 126/126 passed |
| Synthetic regression evaluation | 16/16 passed |
| Frontend lint | Passed |
| Frontend production build | Passed |
| API process and `/` route | Passed |
| OpenAPI document | Passed |
| Frontend development server | Passed |
| Live Exasol connectivity | Blocked—not attempted against an existing deployment |
| Schema setup or seed | Blocked—not authorized against a confirmed disposable database |
| Database-backed incidents, analytics, cascade, and investigation | Unverified because Exasol setup was blocked |
| Complete browser investigation workflow | Unverified because the database-backed endpoints were unavailable |

The production build emitted a non-failing warning that its main JavaScript
chunk was approximately 615 kB before gzip and exceeded Vite's 500 kB warning
threshold. This is a performance follow-up, not a build failure.

## Documentation finding

The deployment guide previously instructed users to run `make database` and
then `make smoke`. The `smoke` target already depends on `database`, and the
`database` target runs `scripts.setup_database --reset`; that sequence would
reset the synthetic schema twice. The guide now instructs users to run only
`make smoke` and explicitly limits it to a confirmed disposable database.

## Limitations and next safe step

This rehearsal proves clean dependency installation, automated verification,
builds, and process startup on one macOS machine. It does not prove Exasol
connectivity or the end-to-end incident workflow. Complete that check only with
an explicitly authorized disposable Exasol Personal deployment, then run
`make smoke` once and append a separate database-verification record.
