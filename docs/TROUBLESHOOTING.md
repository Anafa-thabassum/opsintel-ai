# Troubleshooting

| Symptom | Check | Safe next step |
|---|---|---|
| Exasol unavailable / connection refused | `exasol status --json`; confirm the Personal service is running and the configured DSN is correct. | Start the existing deployment with the Exasol Personal app or `exasol start --wait-timeout-minutes 3`. Check launcher logs. Do not delete volumes or reset storage. |
| Missing Exasol password | Check `EXASOL_PASSWORD` and the configured `EXASOL_SECRETS_PATH`. | For local Personal, let the app read the default `secrets.json`; for another endpoint use a secret manager. Never paste credentials in an issue. |
| TLS/remote connection rejected | Check whether the DSN is loopback and inspect `EXASOL_TLS_VERIFY`. | Set `EXASOL_TLS_VERIFY=true` and configure the trusted certificate for remote connections. The app rejects unverified non-loopback DSNs. |
| Schema/table not found | Run `make memory-check`; confirm the base `OPSINTEL` schema exists. | Run `make database` only when the intended schema is new or existing demo data should be preserved. Run `make memory-migrate` to apply numbered additive migrations. Never edit an applied migration. |
| Backend unavailable | `curl http://127.0.0.1:8000/health`; check the Uvicorn terminal and port. | Start from repository root using `make api`. Check `CORS_ORIGINS` if the browser cannot reach the API. |
| Frontend cannot reach API | Inspect `frontend/.env` and Vite output. | Set `VITE_API_URL=http://127.0.0.1:8000`, restart Vite after changes, and confirm FastAPI CORS includes the exact origin. |
| Frontend install/build fails | Check Node meets Vite's engine requirement (`^20.19.0 || >=22.12.0`) and use the lockfile. | From `frontend/`, run `npm ci`, then `npm run lint` and `npm run build`. |
| LLM unavailable | Check `OPSINTEL_LLM_ENABLED`, backend-only `OPENAI_API_KEY`, model access, timeout, and network. | Leave the feature disabled or use deterministic output. A failed optional summary should not block investigation. No live model access is guaranteed. |
| Invalid incident/run ID | Check `GET /incidents` for available run IDs. | Use an integer run ID from the response; unknown runs return 404. |
| Empty incident memory | `GET /memory/analytics` shows active records; a fresh/empty history can return no candidates. | This is valid and should remain unresolved. Do not seed fake confirmed incidents. A memory candidate requires a real reviewed confirmation. |
| Memory endpoints return 503 | Check `OPSINTEL_AUTH_TOKENS_JSON` is valid non-empty JSON in the backend environment and migrations are applied. | Set grants using a secret manager and restart the backend. Do not put tokens in frontend variables. |
| Unauthorized reviewer / 401 or 403 | Check bearer token, actor role, and `Authorization` header. | Only configured reviewer grants can review/revoke; the submitting actor cannot approve their own submission. Use distinct identities. |
| Concurrent review returns 409 | Another reviewer may already have changed the pending state. | Refresh the submission and its audit history. Do not retry blindly or create a duplicate approval. Exactly one pending-state transition should win. |

Before considering any destructive reset, confirm the deployment and data owner, verify a recoverable backup, and use a separate disposable database. The routine commands in this guide do not require deleting data.
