# Configuration

The root `.env.example` documents backend settings. Python does not automatically load `.env`; export variables in the shell before starting Uvicorn (for example, `set -a; source .env; set +a`). Keep secrets out of source control. `frontend/.env.example` configures Vite.

| Variable | Default | Purpose |
|---|---|---|
| `EXASOL_DSN` | `127.0.0.1:8563` | Exasol endpoint. Non-loopback DSNs require TLS verification. |
| `EXASOL_USER` | `sys` | Local demo user. Use a least-privileged account for any remote deployment. |
| `EXASOL_PASSWORD` | unset | Password; if unset, the local Exasol Personal secrets file is read. |
| `EXASOL_SECRETS_PATH` | `~/.exasol/personal/deployments/default/secrets.json` | Optional local credentials file path. |
| `EXASOL_TLS_VERIFY` | `false` | Allowed without verification only for loopback DSNs; set `true` remotely. |
| `CORS_ORIGINS` | localhost Vite origins | Comma-separated browser origins allowed by FastAPI. |
| `OPSINTEL_AUTH_TOKENS_JSON` | empty | JSON map of bearer tokens to investigator/reviewer actor IDs and roles. Empty disables verified-memory APIs. |
| `OPSINTEL_MEMORY_MIN_SIMILARITY` | `0.42` | Candidate-retrieval threshold in the range 0–1; similarity is not causal probability. |
| `OPSINTEL_LLM_ENABLED` | `false` | Enables optional evidence-grounded narrative summary. |
| `OPENAI_API_KEY` | empty | Backend-only credential for the optional Responses API request. |
| `OPSINTEL_LLM_MODEL` | `gpt-6-luna` | Model identifier sent by the backend. Account availability is not guaranteed. |
| `OPSINTEL_LLM_TIMEOUT_SECONDS` | `10` | Bounded model request timeout. |
| `GITHUB_TOKEN` | empty | Optional server-side GitHub API token to raise public-issue ingestion rate limits. |
| `VITE_API_URL` | `http://127.0.0.1:8000` | Frontend API origin, read by Vite at build/dev time. Do not put secrets in `VITE_*`. |

Example memory grants (use unique random tokens; these placeholders are not credentials):

```json
{
  "<investigator-token>": {"actor_id": "investigator-1", "role": "investigator"},
  "<reviewer-token>": {"actor_id": "reviewer-1", "role": "reviewer"}
}
```

The submitter and reviewer actor IDs must differ. This prototype has no account provisioning, rotation, or enterprise identity integration. See [Security](SECURITY.md).
