# Independent Reviewer Holdout

- Provenance: **independent**
- Independent validation status: **complete**
- Dataset version: `opsintel-review-v1`
- Evaluated at: `2026-10-23T07:04:45+00:00`
- Evaluator version: `2.0`
- Classifier configuration: `deterministic-default-v1`
- Scoring rules: `exact-category-v1`
- Total cases: **19**
- Completed cases: **19**
- Correct findings: **4**
- Incorrect findings: **15**
- Unresolved predictions: **16**
- Missing labels: **0**
- Accuracy on completed cases: **21.1%**
- Dataset SHA-256: `64d766d4782ee94223796e91d79c35fb359d3dcd9de414b1b8ebed41afacf71b`
- Classifier SHA-256: `bc274d54f8f161a2f56388118742ae4dee44a0717687b5caab246fa7467d1c10`
- Cases with complete evidence references: **19/19**
- Outputs that avoided a causation claim: **19/19**
- Frozen ref: `independent-holdout-v1`
- Frozen commit: `47a0831500b9cd0c725c73d2fbdf3603d8f1d234`
- Pseudonymous case authors: reviewer_a, reviewer_b, reviewer_c
- Frozen evaluator SHA-256: `c07b1f2ddcc3b5e1f11447bf8f7aa98501c2f99c5d8f3657106945254d9feb75`

## Scoring rules

Exact category match receives credit; partial category matches receive no credit. Unclassified predictions remain unresolved. Missing labels are reported and excluded from accuracy.
Expected findings and uncertainty are reported separately and do not create partial category credit.

## Category results

| Category | Correct | Total |
|---|---:|---:|
| conflicting_evidence | 0 | 2 |
| delayed_run | 0 | 1 |
| dependency_failure | 0 | 3 |
| duplicate_data | 0 | 1 |
| early_termination | 0 | 2 |
| incomplete_data | 0 | 3 |
| schema_mismatch | 1 | 3 |
| timeout | 2 | 3 |
| unclassified | 1 | 1 |

## Error analysis

The evaluator recorded these misses:

| Case | Expected | Predicted | Evidence reviewed | Next fix to test |
|---|---|---|---|---|
| REV-A-001 | incomplete_data | unclassified | The pipeline run log reports that 850 of 1000 expected records were processed. The job exits successfully, but the downstream completeness check fails because 150 records are missing. No upstream extraction logs are available. | Add the smallest rule or abstention test that separates the expected category without changing this frozen result. |
| REV-A-002 | early_termination | unclassified | The execution log records that the worker process terminated with exit code 137 before the final output was committed. No container memory metrics or orchestrator termination events are available. | Add the smallest rule or abstention test that separates the expected category without changing this frozen result. |
| REV-A-003 | timeout | unclassified | The task log shows a database query started at 10:00 and was cancelled at 10:30 after reaching the configured 30-minute execution limit. The query plan and database performance metrics are unavailable. | Add the smallest rule or abstention test that separates the expected category without changing this frozen result. |
| REV-A-004 | schema_mismatch | unclassified | The ingestion job fails when inserting a string value into a destination column configured as an integer. The error log identifies the affected column and rejected value. No upstream schema-change record is available. | Add the smallest rule or abstention test that separates the expected category without changing this frozen result. |
| REV-A-005 | dependency_failure | unclassified | A transformation task fails because its required upstream table is unavailable. The database reports that the relation does not exist. Deployment history and upstream task execution logs are unavailable. | Add the smallest rule or abstention test that separates the expected category without changing this frozen result. |
| REV-A-006 | delayed_run | unclassified | The scheduled pipeline was configured to start at 08:00 but began at 08:47. The available scheduler log confirms the late start. Scheduler queue metrics and upstream resource availability are missing. | Add the smallest rule or abstention test that separates the expected category without changing this frozen result. |
| REV-A-007 | duplicate_data | unclassified | The destination table contains two records with the same business key and ingestion date. The available query confirms the duplicate keys, but source records, retry logs, and idempotency records are unavailable. | Add the smallest rule or abstention test that separates the expected category without changing this frozen result. |
| REV-A-008 | conflicting_evidence | unclassified | The pipeline summary reports a successful run with 12000 records written, while the validation report for the same run reports 11800 records written. The reports have not been reconciled against execution IDs or timestamps. | Add the smallest rule or abstention test that separates the expected category without changing this frozen result. |
| REV-C-001 | incomplete_data | unclassified | A data quality check expects 5000 records but finds 4720 after the pipeline completes. The check output is available, but source counts, filter conditions, and rejected-record logs are missing. | Add the smallest rule or abstention test that separates the expected category without changing this frozen result. |
| REV-C-002 | early_termination | unclassified | The container orchestration event reports that the task's container was terminated before the completion marker was written. The event does not include a termination reason, and resource metrics are unavailable. | Add the smallest rule or abstention test that separates the expected category without changing this frozen result. |
| REV-C-004 | schema_mismatch | unclassified | A downstream validator rejects a timestamp value because it does not match the configured ISO date-time format. The rejected value and validation error are recorded, but the upstream schema contract is unavailable. | Add the smallest rule or abstention test that separates the expected category without changing this frozen result. |
| REV-C-005 | dependency_failure | unclassified | A transformation reports that a required upstream task has not produced its expected artifact. The orchestration dependency graph is available, but the upstream task's logs and artifact-storage status are missing. | Add the smallest rule or abstention test that separates the expected category without changing this frozen result. |
| CASE001 | incomplete_data | unclassified | Pipeline stopped before all expected records were processed; no explicit termination reason is available. | Add the smallest rule or abstention test that separates the expected category without changing this frozen result. |
| CASE003 | dependency_failure | unclassified | The pipeline failed after the upstream service returned connection errors; independent confirmation is unavailable. | Add the smallest rule or abstention test that separates the expected category without changing this frozen result. |
| CASE005 | conflicting_evidence | unclassified | Two log sources report different failure reasons, and neither reason is independently verified. | Add the smallest rule or abstention test that separates the expected category without changing this frozen result. |

Review the cited cases before changing the rules. Preserve the frozen result and publish any later classifier version as a separate evaluation.

## Missing labels

No ground-truth labels are missing.

## Unresolved predictions

`REV-A-001`, `REV-A-002`, `REV-A-003`, `REV-A-004`, `REV-A-005`, `REV-A-006`, `REV-A-007`, `REV-A-008`, `REV-A-009`, `REV-C-001`, `REV-C-002`, `REV-C-004`, `REV-C-005`, `CASE001`, `CASE003`, `CASE005`

## Scope

Unseen synthetic cases authored by external reviewers and frozen with the tested classifier and evaluator; not a production accuracy estimate.
