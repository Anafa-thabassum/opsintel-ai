# Classifier error analysis v1

## Scope and method

This is a read-only audit of the classifier and the already-published
independent reviewer evaluation. It does not tune rules or change the frozen
dataset, tag, or reports. Case evidence below is transcribed from
`evaluation/independent_holdout_v1.csv`; baseline outcomes are from
`reports/independent-holdout-v1.json` and its Markdown rendering.

The so-called independent holdout is a set of synthetic scenarios written by
three external reviewers. It is independent of the project-authored synthetic
training/evaluation cases, but it is not a sample of real production logs or a
public-data corpus. It is suitable for finding phrase and contract gaps, not
for estimating production accuracy.

## Frozen baseline

| Field | Frozen baseline |
|---|---|
| Classifier configuration | `deterministic-default-v1` |
| Classifier file hash | `bc274d54f8f161a2f56388118742ae4dee44a0717687b5caab246fa7467d1c10` |
| Classifier commit | `47a0831500b9cd0c725c73d2fbdf3603d8f1d234` |
| Independent dataset | `opsintel-review-v1`, 19 cases |
| Dataset hash | `64d766d4782ee94223796e91d79c35fb359d3dcd9de414b1b8ebed41afacf71b` |
| Evaluator / scoring version | `2.0` / `exact-category-v1` |
| Frozen evaluator hash | `c07b1f2ddcc3b5e1f11447bf8f7aa98501c2f99c5d8f3657106945254d9feb75` |
| Exact category matches | 4/19 (21.1%) |
| Incorrect category predictions | 15/19 |
| `unclassified` predictions | 16/19 (84.2%) |
| Complete input reference fields | 19/19, by schema/count check |

The published JSON and Markdown reports agree on 4/19 exact-category accuracy.
The classifier, dataset, and evaluator files match the frozen tag's contents.
The working tree has unrelated changes, but none of those three frozen inputs
is modified.

### Confusion matrix

Each row is the reviewer label and each column is the classifier output.

| Expected \\ Predicted | conflicting | delayed | dependency | duplicate | early termination | incomplete | schema | timeout | unclassified | Total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| conflicting_evidence | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 2 |
| delayed_run | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| dependency_failure | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 3 |
| duplicate_data | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| early_termination | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 2 |
| incomplete_data | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 3 |
| schema_mismatch | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 2 | 3 |
| timeout | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 1 | 3 |
| unclassified | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |

### Per-category metrics

Precision is undefined where the classifier never predicted a category. The
small per-class denominators make all rates descriptive only.

| Category | Support | Predicted | Correct | Precision | Recall |
|---|---:|---:|---:|---:|---:|
| conflicting_evidence | 2 | 0 | 0 | — | 0% |
| delayed_run | 1 | 0 | 0 | — | 0% |
| dependency_failure | 3 | 0 | 0 | — | 0% |
| duplicate_data | 1 | 0 | 0 | — | 0% |
| early_termination | 2 | 0 | 0 | — | 0% |
| incomplete_data | 3 | 0 | 0 | — | 0% |
| schema_mismatch | 3 | 1 | 1 | 100% | 33.3% |
| timeout | 3 | 2 | 2 | 100% | 66.7% |
| unclassified | 1 | 16 | 1 | 6.25% | 100% |

The reviewer expected uncertainty is `candidate_only` in 16 cases and
`unresolved` in 3. From the per-case output, the predicted resolution status
agrees with the reviewer in 6/19 cases: all three intended abstentions and the
three non-abstaining cases. The evaluator does not publish this aggregate.
Thirteen `candidate_only` cases are returned as unresolved. In REV-A-008 and
CASE005 the abstention status is appropriate, but the category should still
describe the explicitly conflicting evidence; REV-A-009 is the one correctly
unclassified case.

## Classifier behavior observed in code

`classify_evidence(log_messages, missing_rows, expected_rows=None,
actual_rows=None)` returns a three-item tuple: category, hypothesis, and next
action. The evaluation wrapper passes only evidence observations as strings
and optional numeric row-count fields. It does not pass evidence types,
references, timestamps, or source identities into classification.

`_classify_evidence_details` lowercases and joins the messages, removes a whole
message if it contains one of a short list of benign phrases, then applies
substring rules in this fixed order: delayed run, duplicate data, timeout,
schema mismatch, dependency failure, early termination, incomplete data.
Positive row-count excess appends `duplicate_data`; positive `missing_rows`
appends `incomplete_data`. The first match wins. Multiple matches reduce the
qualitative confidence to `low`, but still force the first rule's category.
There is one special conflict rule: at least one fixed success phrase and one
fixed failure phrase must both occur in the concatenated text. Otherwise no
match returns low-confidence `unclassified`.

The abstention behavior is conservative in that it does not invent a category
for unknown phrasing. Its current boundary is too narrow: categories depend on
literal vocabulary, and explicitly reported contradictions outside the
success/failure phrase pair also abstain. `missing_rows` is an externally
provided numeric signal; numbers and timing relationships inside prose are
not parsed. Negation handling is an exclusion list, not a general negation
model: a listed phrase suppresses the entire message, while unlisted forms
such as “did not time out” can still match the positive `timeout` substring.

## Case-by-case audit

| Case | Expected → predicted | Evidence and failure type | Finding |
|---|---|---|---|
| REV-A-001 | incomplete_data → unclassified | “850 of 1000” and “150 records are missing”; prose-count extraction and vocabulary | Count fields are blank, and `150 records are missing` does not match `missing rows`, `row shortfall`, or other incomplete-data phrases. “exits successfully” is not one of the success signals. |
| REV-A-002 | early_termination → unclassified | worker “terminated … before the final output was committed”; vocabulary | `terminated` is a broad failure signal but not an early-termination rule by itself. `terminated before completion` does not match the intervening wording. Cause remains unknown, as expected. |
| REV-A-003 | timeout → unclassified | query “cancelled … after reaching the configured 30-minute execution limit”; vocabulary | Rules recognize `time limit`, `deadline exceeded`, and `execution exceeded`, but not “execution limit” or the structured start/cancel duration. |
| REV-A-004 | schema_mismatch → unclassified | string inserted into integer destination column; vocabulary / structured type signal | The classifier recognizes “data type” and “incompatible type”, but not this field/type phrasing. The record does not supply a parsed source/target type pair. |
| REV-A-005 | dependency_failure → unclassified | required upstream table unavailable; database says relation does not exist; vocabulary | No rule covers unavailable upstream relations or missing tables. `fails` is not `failed`, and “relation does not exist” is not recognized. |
| REV-A-006 | delayed_run → unclassified | configured start 08:00, actual start 08:47; structured time signal | The classifier does not parse scheduled and actual timestamps or compare them. The prose does not use any configured delayed-run phrase. |
| REV-A-007 | duplicate_data → unclassified | same business key and ingestion date appears twice; vocabulary / structured duplicate signal | No rule covers duplicate keys or uniqueness-check results; counts are blank, so row-count excess cannot fire. The missing retry/idempotency evidence limits cause claims, not the duplicate symptom label. |
| REV-A-008 | conflicting_evidence → unclassified | successful summary says 12,000 rows; validation says 11,800; conflicting structured values | Conflict detection only checks a fixed success-plus-failure phrase combination. It does not detect contradictory counts or sources. The `unresolved` status itself matches the reviewer intent. |
| REV-A-009 | unclassified → unclassified | generic failed status with no logs, timestamps, counts, or dependency state; insufficient evidence | Correct abstention. This is the clearest genuinely insufficient-evidence case. |
| REV-C-001 | incomplete_data → unclassified | expected 5,000, found 4,720 after completion; prose-count extraction / vocabulary | Numeric values remain embedded in prose and all numeric fields are blank. “expects … but finds …” is not a recognized shortfall phrase. |
| REV-C-002 | early_termination → unclassified | container “terminated before the completion marker was written”; vocabulary | It is semantically close to the rule but does not contain the exact contiguous phrase `terminated before completion`. Termination reason is correctly not inferred. |
| REV-C-003 | timeout → timeout | query exceeded configured 10-minute statement timeout and was cancelled; recognized vocabulary | Correct category and candidate-only status. Missing query plan/resource data appropriately limits root-cause certainty. |
| REV-C-004 | schema_mismatch → unclassified | validator rejects timestamp because it does not match ISO date-time format; vocabulary / structured format signal | The phrase `does not match expected` is narrower than `does not match the configured … format`; format/type validation is not normalized to a schema signal. |
| REV-C-005 | dependency_failure → unclassified | upstream task has not produced required artifact; vocabulary / dependency state | No rule covers a missing/unproduced upstream artifact. The graph alone does not establish why it is missing, so candidate-only rather than confirmed cause is appropriate. |
| CASE001 | incomplete_data → unclassified | “stopped before all expected records were processed”; vocabulary / event extraction | The early-termination rule expects `ended before all expected rows were processed`; incomplete-data rules do not recognize this paraphrase. No explicit cause is available. |
| CASE002 | timeout → timeout | execution exceeded configured time limit; recognized vocabulary | Correct category and candidate-only status. |
| CASE003 | dependency_failure → unclassified | upstream service returned connection errors; vocabulary / signal semantics | The word `errors` sets the broad failure flag but is not a category rule. The upstream relationship is described, but it is not normalized into a dependency signal. |
| CASE004 | schema_mismatch → schema_mismatch | output field type differs from required schema; recognized vocabulary | Correct category and candidate-only status. |
| CASE005 | conflicting_evidence → unclassified | two log sources report different failure reasons; conflict / uncertainty boundary | The special conflict rule requires explicit success and failure signals, not two incompatible reports. Abstention is appropriate because neither reason is verified; the output loses the explicit conflicting-evidence category. |

## Error classes

1. **Vocabulary and phrase coverage (dominant):** Most misses express a known
   symptom in ordinary wording not present in `_CLASSIFICATION_RULES`. This
   includes terminated, cancelled-at-limit, unavailable relation, same-key
   duplicates, unproduced artifacts, and connection errors. Current rule
   tests use canonical phrases and the fixed synthetic challenge vocabulary.
2. **Structured evidence extraction:** The cases contain count pairs,
   timestamps, data types, duplicate-key facts, source identity, and dependency
   relationships as prose. The holdout has blank structured count columns in
   every row. The evaluator does not extract these values before classification.
3. **Conflict semantics:** Two cases explicitly state that sources disagree.
   The success/failure heuristic misses count disagreement and competing
   failure reasons. The intended output can be `conflicting_evidence` while
   remaining unresolved; those are separate dimensions, not mutually
   exclusive outcomes.
4. **Genuinely insufficient evidence:** REV-A-009 should stay `unclassified`.
   Several candidate-only labels still lack verified causes, but they do have
   enough stated evidence for a symptom category. The high unresolved count is
   therefore not solely a justified safety abstention.
5. **Negation and misleading-message risk:** Existing tests cover selected
   benign phrases and a success/failure conflict, not scoped negation,
   misleading log text, multiple sources, or a positive signal negated later
   in the same observation. The benign filter suppresses a whole message, so
   one benign phrase can hide a separate actionable clause.

## What existing tests and evaluations measure

- `tests/test_evaluation.py` checks individual canonical rules and the
  project-authored 16-case synthetic challenge set. It does not measure
  generalization to the reviewer wording.
- `tests/test_investigator.py` checks selected rule precedence, row-count
  helpers, conflicting success/failure text, low/medium qualitative confidence,
  unresolved unknown text, evidence references for candidate output, and
  investigation data assembly. It does not provide paraphrase/negation coverage
  for each category.
- `scripts/evaluate_holdout.py` computes exact category matches and per-expected
  category correct/total counts, records per-case outputs and input strings,
  and checks the frozen data/classifier/evaluator hashes. It does not score
  `expected_findings_json`, and it does not aggregate or report
  `uncertainty_correct`.
- The evaluator's `evidence_traceable` value is `len(evidence_refs) == len(logs)`
  after each evidence object is required to have a reference. This checks input
  shape/count, not whether the classifier's output is tied to those references;
  the classifier API receives no references.
- The evaluator sets `causation_claimed` to `False` as a constant, then counts
  that field to publish 19/19 causation-safe outputs. This is not a semantic
  check of classifier wording or candidate claims.
- `reports/public-corpus-v2.md` records 7/10 on short public Airflow/dbt issue
  excerpts with project-authored mappings. It is useful compatibility evidence,
  not an independently labelled accuracy set.
- `reports/independent-holdout-v1.md` records the frozen exact-category result
  and per-case misses. It does not report a confusion matrix, precision/recall,
  or a summary of uncertainty agreement; those are derived in this audit.
- The human impact protocol defines a 40-trial study, but the judging scorecard
  reports 0/40 trials and 0/4 participants. There is currently no measured
  evidence that OpsIntel reduces investigation time or improves correctness.

## Audit conclusion and handoff

The primary defect is not a single precedence bug. The classifier is a
small substring matcher, while the frozen reviewer cases describe symptoms
through paraphrased text and embedded structured facts. The evaluator also
collapses category identification and abstention into one exact category and
does not validate output evidence grounding or causal wording. Its published
4/19 result is valid for exact category matches under the frozen rules, but its
19/19 causation-safe and reference-completeness counts should be interpreted
as input/schema checks, not semantic validation.

No classifier or evaluator code has been changed in this phase. Phase 2 should
propose component contracts and separate at least these decisions: symptom
category, candidate-only versus unresolved status, and confirmed root cause
(which remains human-only). Architecture changes, label semantics, and
evaluation changes require approval before implementation. Phase 3 should
create a separate development corpus; the frozen reviewer set must remain
untouched and must not be used to tune phrases.
