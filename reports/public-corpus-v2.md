# Public failure-message compatibility evaluation

- Cases: **10**
- Exact category matches: **7/10 (70.0%)**
- Scope: Project-labelled compatibility corpus; not an independent accuracy estimate.
- Inputs: short framework-generated messages from Apache-2.0 repositories; source and licence URLs are recorded per case.
- Limitation: labels were assigned by the OpsIntel project, not external reviewers, and the corpus is small.

## Results

| Case | Project | Expected | Predicted | Confidence | Result |
|---|---|---|---|---|---|
| PUB-AF-001 | Apache Airflow | dependency_failure | unclassified | low | FAIL |
| PUB-AF-002 | Apache Airflow | timeout | timeout | medium | PASS |
| PUB-AF-003 | Apache Airflow | timeout | timeout | medium | PASS |
| PUB-AF-004 | Apache Airflow | unclassified | unclassified | low | PASS |
| PUB-AF-005 | Apache Airflow | unclassified | unclassified | low | PASS |
| PUB-AF-006 | Apache Airflow | timeout | timeout | medium | PASS |
| PUB-AF-007 | Apache Airflow | timeout | timeout | medium | PASS |
| PUB-AF-008 | Apache Airflow | dependency_failure | unclassified | low | FAIL |
| PUB-AF-009 | Apache Airflow | dependency_failure | unclassified | low | FAIL |
| PUB-DBT-001 | dbt-core | unclassified | unclassified | low | PASS |

## Published failures

### PUB-AF-001

- Source: [Apache Airflow](https://github.com/apache/airflow/issues/65942)
- Licence: [Repository code: Apache-2.0; issue-body licensing not separately confirmed](https://github.com/apache/airflow/blob/main/LICENSE)
- Expected `dependency_failure`; predicted `unclassified`.
- Label rationale: Mapped to dependency_failure because the issue reports a missing runtime dependency; the exact import path remains to be verified.
- Interpretation: the current deterministic vocabulary does not recognise this upstream phrasing; no cause was confirmed.

### PUB-AF-008

- Source: [Apache Airflow](https://github.com/apache/airflow/issues/15495)
- Licence: [Repository code: Apache-2.0; issue-body licensing not separately confirmed](https://github.com/apache/airflow/blob/main/LICENSE)
- Expected `dependency_failure`; predicted `unclassified`.
- Label rationale: Mapped to dependency_failure because a third-party runtime package cannot be imported.
- Interpretation: the current deterministic vocabulary does not recognise this upstream phrasing; no cause was confirmed.

### PUB-AF-009

- Source: [Apache Airflow](https://github.com/apache/airflow/issues/30915)
- Licence: [Repository code: Apache-2.0; issue-body licensing not separately confirmed](https://github.com/apache/airflow/blob/main/LICENSE)
- Expected `dependency_failure`; predicted `unclassified`.
- Label rationale: Mapped to dependency_failure because the failure is an unresolved runtime module; path details remain unconfirmed.
- Interpretation: the current deterministic vocabulary does not recognise this upstream phrasing; no cause was confirmed.
