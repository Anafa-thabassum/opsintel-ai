# Verified memory learning curve — pending evidence

No learning-curve points are reported. The repository does not yet contain an independently adjudicated, chronological set of engineer-confirmed incidents and later queries. The two-case public development corpus has no OpsIntel-confirmed causes and cannot be used as memory ground truth. The frozen 19-case reviewer holdout remains excluded from tuning and memory training.

`python -m scripts.evaluate_memory <adjudicated-events.jsonl> --output <report.json>` will emit actual query-by-query memory sizes and retrieval success after a suitable dataset is obtained. The methodology, required event schema, and leakage guards are in `docs/evaluation-methodology.md`. Any future chart must be generated from that output, with the underlying dataset, licence/consent, source provenance, and timestamp basis published.
