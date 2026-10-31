# Incident investigation

## Request path

`GET /investigate/{run_id}` loads the selected run and logs from Exasol, reads the run-health analytical view, compares the run with its latest successful run, and passes the retrieved observations to the deterministic evidence classifier and candidate assessor. The response preserves observations, evidence references, classification status, candidate explanations, and an optional narrative summary. `GET /investigate/{run_id}/root-causes` returns the deterministic assessment.

## Supported symptoms

The classifier recognizes the operational categories `delayed_run`, `duplicate_data`, `timeout`, `schema_mismatch`, `dependency_failure`, `early_termination`, and `incomplete_data`. It can also return `conflicting_evidence` when support and negation conflict, or `unclassified` when evidence does not support a category. These describe symptoms/category support. They do not establish why the underlying event happened.

Evidence normalization preserves original observations and references and attempts safe extraction of timestamps, counts, exit codes, dependency states, and other structured fields. Malformed or absent values do not become confident evidence. Text cues are combined with structured signals; negation and contradictory signals are evaluated. When several categories match, all supported symptoms remain available and the displayed category uses evidence strength, number of independent references, and the documented `CATEGORY_ORDER` as a deterministic tie-break. Material conflict blocks a reliable category decision.

Candidate explanations are separate from observed symptoms. The classifier does not independently set `confirmed_root_cause`. The optional LLM can only produce a narrative about retrieved facts; it cannot override the classifier, invent evidence, confirm a cause, or execute recovery.

## Interpretation and limits

- `candidate_only` means evidence supports a symptom/category, with no confirmed root cause. It does not mean the incident is resolved.
- `unresolved` means available evidence is insufficient or materially ambiguous.
- `confirmed_root_cause` is reserved for approved reviewer workflow after all policy gates pass; the criteria have not been empirically validated as proof of causation.
- An Exasol dependency cascade is a time-bounded correlation, not proof of an upstream causal relationship.
- Metrics and public issue labels retain their provenance; the frozen 19-case result remains 4/19.

For HTTP fields and schemas see [API reference](API_REFERENCE.md); for evaluation provenance see [reproducibility report](../reports/reproducibility-and-evaluation.md).
