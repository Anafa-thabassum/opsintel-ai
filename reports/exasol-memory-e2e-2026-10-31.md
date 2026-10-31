# Exasol Verified Incident Memory runtime check

**Run date:** 2026-10-31 (Asia/Kolkata)  
**Purpose:** Diagnose the local Exasol connection refusal and exercise schema initialization, submission, review, persistence, retrieval, concurrency, and audited revocation.  
**Scope:** One local end-to-end check using source excerpts from the public Apache Airflow issue listed below. This is a functional smoke check, not a benchmark, corpus evaluation, or human-factors study.

## Runtime blocker and safe recovery

The application initially could not connect to `127.0.0.1:8563` (`ConnectionRefusedError`). The Exasol Personal launcher (`exasol`, version 2.3.0) reported the deployment as stopped, even though its local deployment metadata retained stale running/workflow state. The deployment logs showed a prior stop/poweroff; its VM had been started, but no guest service was accepting connections on port 8563. Docker Desktop was available (Docker 29.9.2, server running); its container list had no Exasol container. Exasol Personal uses its own local VM here, so the absence of an Exasol Docker container was not the cause.

Safe recovery used the documented launcher command:

```sh
exasol start --wait-timeout-minutes 3
```

It started the existing local deployment and reported that the database was ready. No volume was deleted, no reset/redeploy was requested, and no existing data was removed. There is no remaining Exasol connectivity blocker in this run.

## Environment and reproducibility

- Host: macOS Darwin 25.6, Apple Silicon `arm64`.
- Exasol Personal: launcher 2.3.0; local preset, one node, VM configured with 2 CPUs and 8192 MB RAM.
- Exasol DBMS startup event: `2026.2.0-nano.3`.
- Database endpoint/user: `127.0.0.1:8563`, `sys`; local Personal credentials were read through the app's existing credential loader and are not included here.
- App: repository `.venv`, FastAPI/Uvicorn, loopback test server on port 49973. Random temporary bearer tokens existed only in the process environment; actor IDs were explicitly test actors.
- Default match threshold: 0.42 (`OPSINTEL_MEMORY_MIN_SIMILARITY` unset).
- No latency benchmark was run. Resource configuration above is environment context, not a performance claim.

Useful commands:

```sh
exasol status --json
exasol start --wait-timeout-minutes 3
make memory-check
```

`make memory-check` then connected and reported no pending migrations (`pending: []`); migration `001_verified_incident_memory.sql` and `002_public_incidents.sql` were present/applied. `GET /health` returned `{"status":"healthy","database":"connected"}`.

## Data provenance and test records

Evidence source: [Apache Airflow issue #36734](https://github.com/apache/airflow/issues/36734), accessed 2026-10-31. The issue contains the S3 sensor timeout trace, including `AirflowSensorTimeout`, a configured 10-second timeout, and a reported 10.264439-second run. A differently worded deferrable/reschedule excerpt from the same issue provided the retrieval query.

For database workflow testing, the two source excerpts were inserted into local pipeline telemetry under test-only run IDs:

| Run ID | Test record name | Use |
|---:|---|---|
| 3673401 | `public_e2e_airflow_36734_reschedule_attempt` | Submission and reviewer confirmation source |
| 3673402 | `public_e2e_airflow_36734_deferrable_attempt` | Differently worded similarity query |

These are test records mapped from one cited issue, not independent production runs, independent incidents, or a separate evaluation set. Row-count fields were NULL; none were invented. Database writes for these two test telemetry rows and their corresponding log rows remain in the local database so the reproduction can be inspected. The temporary memory confirmation was revoked through the normal audited API and its historical record retained.

## Observed workflow outcomes

1. `GET /investigate/3673401` returned the timeout investigation.
2. `POST /memory/submissions` returned 201 and created one pending hypothesis with internal log reference `OPSINTEL.PIPELINE_LOGS · LOG-36734011` and the public issue URL.
3. Two different reviewer test actors submitted approval concurrently for the same pending submission. Responses were one HTTP 200 and one HTTP 409 (`Submission was reviewed concurrently`). The ordering in the captured server log was 200 followed by 409; exactly one reviewer transition won.
4. SQL immediately after the race showed one submission, one confirmation, and one `confirmed` audit event. The confirmed row used reviewer test actor `e2e-reviewer-test-b`; this verifies the role/state mechanics, not independent human adjudication.
5. The first API process was stopped. A second process connected to the same Exasol database. `GET /memory/incidents/3673401` returned the confirmed memory and evidence references, proving persistence across application restart.
6. After clearing the threshold override, `GET /memory/similar/3673402` returned the historical incident at score **0.5855**, above the default threshold **0.42**. The candidate cited both the historical pipeline log and the Airflow issue. It was correctly labelled a candidate requiring engineer verification; similarity was not represented as causal proof.
7. The temporary test confirmation was revoked using `POST /memory/incidents/f0cbc67a-4e4f-4320-9476-8ea5508f7adb/revoke`. The endpoint returned 200 and `status=revoked`.

## Read-only SQL evidence after audited revocation

Queries were run directly using the repository's existing Exasol connection helper. Results:

```text
confirmed_incident:
  ('f0cbc67a-4e4f-4320-9476-8ea5508f7adb', 3673401,
   'timeout', 'revoked', 1, 'e2e-reviewer-test-b')
audit_actions:
  ('confirmed', 'e2e-reviewer-test-b', 'Test-only reviewer checked the public source trace and the versioned timeout criteria; this confirms the timeout mechanism only.')
  ('revoked', 'e2e-reviewer-test-b', 'Temporary E2E test confirmation revoked after workflow verification; test actor only.')
submission_count:
  1
match_status:
  (3673402, 'f0cbc67a-4e4f-4320-9476-8ea5508f7adb', 'stale', 1)
source_runs:
  (3673401, 'public_e2e_airflow_36734_reschedule_attempt', 'FAILED', NULL, NULL)
  (3673402, 'public_e2e_airflow_36734_deferrable_attempt', 'FAILED', NULL, NULL)
```

The concurrent review check was performed before revocation: one active confirmation and one confirmation audit were observed. The final SQL above shows the additional single revocation audit, the retained revoked row, and its match invalidated to `stale`. No duplicate confirmation or duplicate audit was produced by the race.

## Captured application logs

The sanitized local Uvicorn logs are at:

- `/private/tmp/opsintel-memory-e2e-2026-10-31.log` — submission, concurrent 200/409 reviews, restart, and candidate retrieval.
- `/private/tmp/opsintel-memory-e2e-default-threshold.log` — retrieval after clearing the threshold override.
- `/private/tmp/opsintel-memory-finalize-2026-10-31.log` — final default-threshold retrieval and audited revoke.

These logs contain no bearer tokens. They are temporary host files and are not committed as repository artifacts; this report records the durable results and exact identifiers.

## Limits

- The concurrent actors were separate test tokens, not authenticated human identities. The policy's role separation and atomic state transition were exercised; an authorized human's judgment was not.
- The two telemetry records derive from one public issue and cannot establish generalization or learning-curve performance.
- No Exasol throughput/latency benchmark, larger-history stress run, full browser UI rehearsal, or participant study was performed.
- Confirmation criteria are approved design policy, not empirically validated causal criteria.
- The test telemetry and revoked memory/audit trail remain in local Exasol for reproducibility. No data cleanup was performed.
