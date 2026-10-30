PYTHON := .venv/bin/python

.PHONY: setup database database-reset memory-check memory-migrate smoke impact-study-database api frontend verify evaluate public-evaluate public-evaluate-v2 holdout independent-holdout impact exasol-proof benchmark benchmark-compare submission-check

setup:
	python3 -m venv .venv
	$(PYTHON) -m pip install -r requirements.txt
	cd frontend && npm ci

database:
	$(PYTHON) -m scripts.setup_database

database-reset:
	$(PYTHON) -m scripts.setup_database --reset

memory-check:
	$(PYTHON) -m scripts.migrate_database

memory-migrate:
	$(PYTHON) -m scripts.migrate_database --apply

smoke: database-reset
	$(PYTHON) -m scripts.smoke_exasol

impact-study-database: database-reset
	$(PYTHON) -m scripts.setup_impact_study

api:
	$(PYTHON) -m uvicorn app.main:app --reload

frontend:
	cd frontend && npm run dev

verify:
	$(PYTHON) -m pytest -q
	$(PYTHON) -m tests.run_evaluation
	cd frontend && npm run lint
	cd frontend && npm run build

evaluate:
	$(PYTHON) -m tests.run_evaluation

public-evaluate:
	$(PYTHON) -m scripts.evaluate_public_corpus

public-evaluate-v2:
	$(PYTHON) -m scripts.evaluate_public_corpus evaluation/public_failure_corpus_v2.csv --output reports/public-corpus-v2.json --markdown-output reports/public-corpus-v2.md

holdout:
	$(PYTHON) -m scripts.evaluate_holdout evaluation/frozen_holdout_v1.csv

independent-holdout:
	@test -n "$(FILE)" -a -n "$(REF)" || (echo "Usage: make independent-holdout FILE=evaluation/independent_holdout_v1.csv REF=independent-holdout-v1" && exit 2)
	$(PYTHON) -m scripts.evaluate_holdout "$(FILE)" --provenance independent --frozen-ref "$(REF)" --output reports/independent-holdout-v1.json --markdown-output reports/independent-holdout-v1.md

impact:
	@test -n "$(FILE)" -a -n "$(RECRUITMENT)" || (echo "Usage: make impact FILE=/path/to/results.csv RECRUITMENT=/path/to/recruitment.md" && exit 2)
	$(PYTHON) -m scripts.summarize_impact_study "$(FILE)" --recruitment "$(RECRUITMENT)" --output reports/impact-study-v1.json --markdown-output reports/impact-study-v1.md

exasol-proof:
	$(PYTHON) -m scripts.exasol_proof

benchmark:
	$(PYTHON) -m scripts.benchmark_exasol

benchmark-compare:
	$(PYTHON) -m scripts.benchmark_databases --output reports/database-comparison.json --chart reports/database-comparison.svg

submission-check:
	$(PYTHON) -m scripts.verify_submission
