PYTHON := .venv/bin/python

.PHONY: setup database impact-study-database api frontend verify evaluate holdout impact exasol-proof benchmark

setup:
	python3 -m venv .venv
	$(PYTHON) -m pip install -r requirements.txt
	cd frontend && npm ci

database:
	$(PYTHON) -m scripts.setup_database --reset

impact-study-database: database
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

holdout:
	$(PYTHON) -m scripts.evaluate_holdout evaluation/frozen_holdout_v1.csv

impact:
	@test -n "$(FILE)" || (echo "Usage: make impact FILE=/path/to/results.csv" && exit 2)
	$(PYTHON) -m scripts.summarize_impact_study "$(FILE)" --output reports/impact-study-v1.json

exasol-proof:
	$(PYTHON) -m scripts.exasol_proof

benchmark:
	$(PYTHON) -m scripts.benchmark_exasol
