# Classifier failure analysis — Priority 1 baseline

## Baseline and scope

Read-only audit of the deterministic classifier and its API/evaluation path.
The detailed source evidence, classifier behavior, prior test coverage and
limitations are also recorded in
[`classifier-error-analysis-v1.md`](classifier-error-analysis-v1.md); this
report records the current reproducibility check and maps every independent
case to its principal failure mechanism. The frozen holdout labels were read
for analysis only and were not changed or used to tune the classifier.

The independent evaluator reproduced **4/19 exact matches (21.1%)**, **15
incorrect predictions**, and **16 unresolved predictions**. Dataset,
classifier, and evaluator hashes matched their frozen values:

| Asset | SHA-256 |
|---|---|
| `evaluation/independent_holdout_v1.csv` | `64d766d4782ee94223796e91d79c35fb359d3dcd9de414b1b8ebed41afacf71b` |
| `app/investigator.py` | `bc274d54f8f161a2f56388118742ae4dee44a0717687b5caab246fa7467d1c10` |
| `scripts/evaluate_holdout.py` | `c07b1f2ddcc3b5e1f11447bf8f7aa98501c2f99c5d8f3657106945254d9feb75` |

The existing unit suite passed: **137 passed**. No classifier or evaluator
implementation was changed. The evaluator was invoked without output-path
arguments, so historical report files were not regenerated. No live database,
benchmark, or LLM operation was performed.

## Case-by-case diagnosis

The exact evidence text for each case remains in the frozen CSV and the
case-level audit linked above. The recommended corrections below are design
directions only; the frozen cases must not become tuning examples.

| Case | Expected → predicted | Principal failure and evidence missed | Smallest correction to test on approved development data |
|---|---|---|---|
| `REV-A-001` | `incomplete_data` → `unclassified` | Counts and a missing-record count appear only in prose; evaluator supplies no structured counts and the phrases miss current rules. | Parse validated count expressions into referenced typed facts; preserve ambiguity if denominator/scope is unclear. |
| `REV-A-002` | `early_termination` → `unclassified` | Exit code 137 and process termination before commit are not recognized as the category's existing phrases; no evidence establishes why termination occurred. | Normalize terminal state/exit code as a symptom signal; keep cause unconfirmed. |
| `REV-A-003` | `timeout` → `unclassified` | “Execution limit” plus start/cancel times is not one of the literal timeout phrases. | Extract run-scoped time limit and cancellation facts; distinguish timeout symptom from why it occurred. |
| `REV-A-004` | `schema_mismatch` → `unclassified` | String-to-integer insertion mismatch is expressed as a value and destination type, not recognized phrase. | Normalize explicit source/value and destination type incompatibility with a source reference. |
| `REV-A-005` | `dependency_failure` → `unclassified` | Required upstream relation is unavailable and the database says it does not exist; these phrases are absent from dependency rules. | Extract required relation/dependency state; do not infer upstream cause from relation absence alone. |
| `REV-A-006` | `delayed_run` → `unclassified` | Scheduled 08:00 and actual 08:47 are embedded in prose and never compared. | Extract timestamps with timezone/clock basis and require an applicable schedule/SLA threshold. |
| `REV-A-007` | `duplicate_data` → `unclassified` | Duplicate business keys are explicit, but current rule checks only narrow phrases; retry/lineage facts are absent. | Treat validated same-scope key repetition as symptom evidence; do not infer the duplication mechanism. |
| `REV-A-008` | `conflicting_evidence` → `unclassified` | Two sources give incompatible written counts. Conflict detector only looks for success and failure keywords. | Detect contradictions over the same run, metric, and scope; cite both reports and remain unresolved pending reconciliation. |
| `REV-A-009` | `unclassified` → `unclassified` | Generic failure state with no logs, times, counts, or dependency evidence. | Preserve this abstention behavior. |
| `REV-C-001` | `incomplete_data` → `unclassified` | Expected 5,000 versus observed 4,720 is prose; fields are blank and “expects … finds …” is not recognized. | Normalize comparable expected/actual counts and scope; do not assert why records are absent. |
| `REV-C-002` | `early_termination` → `unclassified` | Container termination before a completion marker is stated, but not with a contiguous recognized phrase. | Normalize termination and completion-marker state; keep unknown termination reason missing. |
| `REV-C-003` | `timeout` → `timeout` | Configured statement timeout and cancellation match current timeout vocabulary. | Retain; candidate cause remains unconfirmed without query/lock/resource evidence. |
| `REV-C-004` | `schema_mismatch` → `unclassified` | Timestamp rejected against configured ISO format; current schema phrases do not cover format-contract mismatch. | Normalize validator, field, value format, and required format as typed schema evidence. |
| `REV-C-005` | `dependency_failure` → `unclassified` | Required upstream artifact was not produced; current rule does not recognize this dependency state. | Represent dependency identity and artifact availability; do not claim why it is missing. |
| `CASE001` | `incomplete_data` → `unclassified` | Processing stopped before expected records were complete; phrase is close to but not equal to the early-termination rule. Category boundary between incomplete data and early termination may itself be ambiguous. | Define symptom precedence/secondary symptoms in the approved taxonomy; adjudicate only on development data. |
| `CASE002` | `timeout` → `timeout` | Explicit configured time-limit exceedance matches current rule. | Retain as a positive timeout regression on development data, not as a tuneable holdout row. |
| `CASE003` | `dependency_failure` → `unclassified` | Upstream service connection errors are described, but the classifier does not normalize the relationship or transport failure. | Extract referenced upstream state and temporal relation; avoid treating correlation alone as confirmed cause. |
| `CASE004` | `schema_mismatch` → `schema_mismatch` | Output type differs from the required schema; existing schema phrase matches. | Retain; require source references and separate schema symptom from any unproven producer change. |
| `CASE005` | `conflicting_evidence` → `unclassified` | Two sources report different reasons; conflict detector requires explicit success and failure terms. | Treat conflicting source claims as a separate evidence dimension, preserve both, and abstain from cause selection. |

## Shared defects and design implications

1. **Narrow string matching:** most misses are familiar symptoms expressed in
   different vocabulary. A larger synonym list alone would remain brittle.
2. **No normalization of structured signals:** prose counts, times, types,
   exit state, duplicate keys, and dependency identity are not extracted into
   typed facts. The evaluation interface passes observations and optional
   numeric fields only.
3. **Conflict is conflated with a specific keyword pair:** incompatible counts
   and competing source explanations should be assessed independently of the
   operational symptom category.
4. **Single-category precedence hides overlap:** fixed rule order selects the
   first match. Row-count excess is also treated as duplicate data, although
   excess alone does not prove duplicate keys.
5. **Negation is coarse:** a short benign-phrase list suppresses an entire
   message, while unlisted negation may still match a positive keyword.
6. **Evidence tracing is post-hoc:** the evaluator checks that input evidence
   references exist by count, while classification receives no references.
   The assessor can manufacture `EVIDENCE-{index}` references when source IDs
   are missing; that is not provenance.
7. **Uncertainty metrics are incomplete:** exact-category score is 4/19 and
   the evaluator derives uncertainty from whether the category is
   `unclassified`; it does not score expected findings or aggregate
   uncertainty agreement. Its `causation_claimed=false` field is constant,
   not a semantic claim audit.

The highest-value direction is the previously approved architecture: preserve
raw evidence and provenance, extract typed signals with polarity and scope,
assess conflicts separately, expose supported symptoms and multiple
candidates, and abstain when required evidence is absent. Keep historical
features and dependency correlations as context, not causal proof. The
classifier must not confirm root causes; the authorized-reviewer policy and
seven class-specific verification criteria remain approved design policies
that have not been empirically validated.

## Gate before implementation

The separate public development corpus is present at
[`evaluation/public_development_corpus_v1.jsonl`](../evaluation/public_development_corpus_v1.jsonl), with its
methodology at
[`public-development-corpus-v1.md`](public-development-corpus-v1.md). It has
two cases, one of which is explicitly ambiguous; the other has an individual
record-page access gap. Both still need independent review, and the first must
be re-fetched before tuning. This audit does not constitute approval of that
corpus or its quality. Per the prior approval gate, implementation remains
paused pending the user's explicit corpus approval (or direction to revise or
replace the corpus first).
