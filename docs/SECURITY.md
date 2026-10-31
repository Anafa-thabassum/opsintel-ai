# Security and data handling

OpsIntel is a hackathon prototype, not a production-secured incident platform.

## Access boundaries

- Verified-memory routes require configured bearer grants for `investigator` or `reviewer`. Role separation and no self-approval are enforced in the API.
- The landing-page email/demo gate is a browser presentation feature, not authentication.
- Most investigation and analytics routes do not require API authentication and may return log evidence. Do not expose the development server to an untrusted network.
- Use TLS and an access-controlled reverse proxy before a controlled deployment. CORS is not authentication.

## Secrets and logs

- Keep Exasol credentials, `OPSINTEL_AUTH_TOKENS_JSON`, `OPENAI_API_KEY`, and `GITHUB_TOKEN` on the backend in a secret manager or ignored local `.env`; never commit them.
- Never put a secret in a `VITE_*` variable; Vite values are built into browser assets.
- The default local demo uses `sys`; remote deployments should use a least-privileged Exasol user and `EXASOL_TLS_VERIFY=true`.
- API request logs include request IDs, route templates, status, and latency, but not request bodies, bearer tokens, or excerpts. Avoid sending sensitive incident data to logs or reports.

## External data

The optional LLM sends selected evidence to the configured OpenAI API. It is disabled by default; confirm data handling, account access, and policy before enabling. Public issue ingestion obtains user-generated GitHub content. A repository's code license does not establish a license for issue-body text; preserve source URLs and license uncertainty.

## Reporting

Report vulnerabilities privately through the repository's GitHub security-advisory process. Do not publish credentials, production logs, personal information, or a live exploit in an issue. The root [SECURITY.md](../SECURITY.md) is the GitHub-facing policy.
