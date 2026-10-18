# Contributing

1. Create a focused branch and keep synthetic data free of secrets.
2. Run `python -m pytest -q` and `python -m tests.run_evaluation`.
3. Run `npm run lint` and `npm run build` from `frontend/`.
4. Explain user-visible changes and any new evidence claims in the pull request.

Do not convert candidate explanations into confirmed root causes without a
separate verification source. New classification rules should include at least
one positive and one false-positive regression case.
