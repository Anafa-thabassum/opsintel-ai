# Public failure-message compatibility evaluation

- Cases: **9**
- Exact category matches: **6/9 (66.7%)**
- Scope: Project-labelled compatibility corpus; not an independent accuracy estimate.
- Inputs: short framework-generated messages from Apache-2.0 repositories; source and licence URLs are recorded per case.
- Limitation: labels were assigned by the OpsIntel project, not external reviewers, and the corpus is small.

## Results

| Case | Project | Expected | Predicted | Confidence | Result |
|---|---|---|---|---|---|
| spark-result-lost | Apache Spark | unclassified | unclassified | low | PASS |
| spark-executor-lost | Apache Spark | unclassified | unclassified | low | PASS |
| spark-executor-shutdown | Apache Spark | early_termination | unclassified | low | FAIL |
| spark-unknown | Apache Spark | unclassified | unclassified | low | PASS |
| spark-fetch-failed | Apache Spark | dependency_failure | unclassified | low | FAIL |
| airflow-upstream-failed | Apache Airflow | dependency_failure | unclassified | low | FAIL |
| airflow-task-failed | Apache Airflow | unclassified | unclassified | low | PASS |
| dbt-unexpected-null | dbt-common | unclassified | unclassified | low | PASS |
| dbt-compilation-error | dbt-common | unclassified | unclassified | low | PASS |

## Published failures

### spark-executor-shutdown

- Source: [Apache Spark](https://github.com/apache/spark/blob/master/core/src/main/scala/org/apache/spark/TaskEndReason.scala)
- Licence: [Apache-2.0](https://github.com/apache/spark/blob/master/LICENSE)
- Expected `early_termination`; predicted `unclassified`.
- Label rationale: The framework explicitly reports termination caused by executor shutdown.
- Interpretation: the current deterministic vocabulary does not recognise this upstream phrasing; no cause was confirmed.

### spark-fetch-failed

- Source: [Apache Spark](https://github.com/apache/spark/blob/master/core/src/main/scala/org/apache/spark/TaskEndReason.scala)
- Licence: [Apache-2.0](https://github.com/apache/spark/blob/master/LICENSE)
- Expected `dependency_failure`; predicted `unclassified`.
- Label rationale: Spark defines this as failure to fetch shuffle data from a remote node requiring earlier-stage work.
- Interpretation: the current deterministic vocabulary does not recognise this upstream phrasing; no cause was confirmed.

### airflow-upstream-failed

- Source: [Apache Airflow](https://github.com/apache/airflow/blob/main/airflow-core/docs/security/audit_logs.rst)
- Licence: [Apache-2.0](https://github.com/apache/airflow/blob/main/LICENSE)
- Expected `dependency_failure`; predicted `unclassified`.
- Label rationale: The event definition explicitly identifies an upstream failure.
- Interpretation: the current deterministic vocabulary does not recognise this upstream phrasing; no cause was confirmed.
