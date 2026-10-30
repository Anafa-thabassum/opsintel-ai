# Contributing

For application, database, evaluation, security, or submission changes, follow
the [architecture-first engineering workflow](docs/engineering-workflow.md) and
complete its [change-plan template](docs/templates/change-plan.md) before
starting significant implementation. Keep the scope focused and obtain human
approval before changing architecture, contracts, evaluation methodology, or
submission claims.

1. Create a focused branch and keep synthetic data free of secrets.
2. Run `python -m pytest -q` and `python -m tests.run_evaluation`.
3. Run `npm run lint` and `npm run build` from `frontend/`.
4. Explain user-visible changes and any new evidence claims in the pull request.

Do not convert candidate explanations into confirmed root causes without a
separate verification source. New classification rules should include at least
one positive and one false-positive regression case.

## Good first contributions

- Add a new synthetic unknown or conflicting-evidence regression case.
- Improve an empty, loading, or database-disconnected dashboard message.
- Add another exported-JSON orchestrator sample without introducing a live
  service dependency.
- Clarify a setup step that failed in a clean clone.

Larger validation work is tracked in [`docs/roadmap.md`](docs/roadmap.md).
