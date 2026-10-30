# Security policy

OpsIntel AI is a hackathon prototype and should be run only with synthetic or
approved non-sensitive data. Do not expose the development server directly to
the public internet.

Report a vulnerability privately through GitHub's security-advisory feature.
Do not include credentials, production logs, or personal data in an issue.

Verified-memory endpoints require explicit bearer-token grants for investigator
and reviewer roles. This is a controlled-demo boundary, not production account
management. Before public deployment, add enterprise identity, token rotation,
rate limiting, audited retention, access logging without evidence payloads,
secret management, dependency scanning, and threat modelling. Run the app
behind TLS; remote Exasol DSNs already require certificate verification.

The email-only demo gate does not authenticate API calls. The existing
investigation endpoints may return incident logs without a bearer token, so
do not expose them to untrusted networks or use sensitive production records.
Memory packets should contain only the minimum necessary source excerpts.

The optional LLM summary sends the selected incident evidence to the configured
OpenAI model. Review data-handling requirements before enabling it, keep the API
key in the backend secret store, and do not send production logs containing
credentials, personal data, or other restricted information.
