# Contributing

Thanks for considering a contribution. Keep changes focused and preserve evaluation provenance.

## Before changing behavior

- Read [Architecture](docs/ARCHITECTURE.md), [Data flow](docs/DATA_FLOW.md), [Security](SECURITY.md), and [Evaluation methodology](docs/evaluation-methodology.md).
- For significant work, follow the [engineering workflow](docs/engineering-workflow.md) and complete `docs/templates/change-plan.md`.
- Do not modify frozen datasets, labels, hashes, or historical reports to improve a new result. Add a new versioned set/report instead.
- Do not claim root-cause confirmation, independent validation, participant benefit, or performance gains without evidence.

## Development checks

From the repository root:

```bash
make verify
```

This runs pytest, the predefined synthetic challenge, Oxlint, and the Vite build. For a focused check, use the relevant pytest module, then lint/build if frontend files changed. `make verify` does not require Exasol.

Database-backed work needs an explicitly authorized disposable Exasol Personal instance. Use additive migrations. Do not run `make database-reset` or `make smoke` against any database containing data to preserve. Never commit `.env`, tokens, credentials, personal data, or sensitive incident excerpts.

## Pull requests

- Explain behavior changes, data/provenance changes, verification commands, and limitations.
- Include source-backed positive and negative cases for classifier behavior; preserve abstention and human-review boundaries.
- Update relevant documentation and the completion ledger when a documented milestone changes.
- Include screenshots only when they show the actual current application; redact credentials and sensitive records.

Good first contributions include documentation fixes, empty/error-state improvements, and synthetic classifier regression cases that are clearly marked as synthetic.
