# Security policy

OpsIntel AI is a hackathon prototype and should be run only with synthetic or
approved non-sensitive data. Do not expose the development server directly to
the public internet.

Report a vulnerability privately through GitHub's security-advisory feature.
Do not include credentials, production logs, or personal data in an issue.

Before production use, add authentication, authorization, audited retention,
TLS verification, secret management, dependency scanning, and threat modelling.

The optional LLM summary sends the selected incident evidence to the configured
OpenAI model. Review data-handling requirements before enabling it, keep the API
key in the backend secret store, and do not send production logs containing
credentials, personal data, or other restricted information.
