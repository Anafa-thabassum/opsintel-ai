# Evaluation methodology

> Current consolidated metrics, dataset hashes, benchmark details, and limitations are in [the reproducibility and evaluation record](../reports/reproducibility-and-evaluation.md). This page describes evaluator protocols; it does not replace any frozen result.

The independent 19-case reviewer holdout, frozen evaluator, and historical 4/19 report remain unchanged. The previously reported 15/19 result reused that reviewer set and is a development comparison, not fresh independent validation. The two-case public development corpus V2 is for development checks only; it has provisional labels and does not contain confirmed incident memory.

`scripts/evaluate_memory.py` accepts a separately curated chronological JSONL event stream. Each event has a unique `event_id`, `event_type` (`confirmation` or `query`), timezone-aware ISO `timestamp`, `run_id`, and an `incident` object with the same run ID and source-backed `evidence`. Confirmation events also require a stable `cause_id`. Query events may include independently adjudicated `expected_category` and `expected_cause_id`; null cause IDs are negative examples. The evaluator rejects duplicate confirmation runs, excludes self-matches, and allows only confirmations strictly earlier than a query. Do not feed hidden reviewer labels to development or threshold selection.

The script reports classifier category accuracy, per-category precision/recall, confusion matrix, forced memory top-1/top-3 cause retrieval, thresholded memory accuracy, false-match rate, abstention, coverage, selective accuracy, Wilson 95% intervals, and a measured learning curve by available memory size. The configured `OPSINTEL_MEMORY_MIN_SIMILARITY` value is included in each report; the 0.42 default is not calibrated because no verified-cause query set exists. A similarity score is never used as classification confidence. Run `python -m scripts.evaluate_memory path/to/adjudicated_events.jsonl --output reports/memory-evaluation.json` and then `python -m scripts.plot_learning_curve reports/memory-evaluation.json --output reports/learning-curve.svg` only after an independent, provenance-tracked event stream exists. The repository currently has no such stream, so it publishes **no memory accuracy or learning-curve numbers**.

Time savings require a participant study. The approved protocol and templates are in `reports/impact-study-protocol.md` and `evaluation/`. No participant outcomes are inferred from synthetic regression tests. Use the existing study tooling only with consented real observations. Report slower and less accurate assisted investigations as well as any benefits.

The new Exasol public mode reports collected count, project-labelled count,
exact category matches against those labels, unresolved rate, and source
reference coverage. It is not a new independent evaluation: the same ten
project mappings came from the historical public scorecard, and short excerpts
can lose relevant context. `false_match_rate` remains null because there are
no independently verified public causes. Run `make public-data-evaluate` only
against an explicitly ingested local Exasol collection; its output is a new
report, separate from historical evaluation assets.
