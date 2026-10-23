# Holdout evaluation

## Licensed public failure-message corpus

`public_failure_corpus_v1.csv` contains nine short framework-generated messages
from Apache Spark, Apache Airflow, and dbt-common. Every row records its exact
source URL, Apache-2.0 licence URL, expected OpsIntel category, and the project's
labelling rationale. Reproduce the compatibility score and published failures
with:

```bash
make public-evaluate
```

This corpus tests unfamiliar upstream vocabulary; it is not production log data
and its labels were assigned by the OpsIntel project. It therefore does not
replace the external-reviewer holdout below or establish independent accuracy.

For the planned 30–50-case expansion, collect only messages whose source page
is publicly reachable and whose repository licence is recorded. Keep one row
per incident message with the exact excerpt, source URL, licence URL, expected
category, and a short labelling rationale. Before tuning the classifier, copy
10–15 rows into a separately versioned holdout file, record the collection
commit, and do not use those rows to change the rules. The current repository
contains the nine-case v1 compatibility corpus; no larger issue/CI collection
is claimed until those provenance checks and labels have been completed.

The supplied issue-linked starter is preserved as
`public_failure_corpus_v2.csv`. It contains 10 Airflow/dbt cases, preserves
each source-specific label, and documents the mapping into OpsIntel's taxonomy.
Its project-labelled score is 7/10; reproduce it with `make public-evaluate-v2`.
This remains compatibility evidence, not an independent accuracy estimate.

## Published versioned holdout

`frozen_holdout_v1.csv` contains 27 project-authored synthetic cases that are
separate from the 16-case regression suite. It covers all nine classifier
outcomes with three cases per expected category.

The published report records the dataset hash, classifier hash, classifier
commit, category totals, and every prediction. The dataset and result first
entered Git history together, so v1 does not independently prove pre-run label
freezing:

- `reports/frozen-holdout-v1.md`
- `reports/frozen-holdout-v1.json`

Reproduce it with:

```bash
make holdout
```

Do not edit v1. Add a new versioned dataset if cases or labels change. This is
a project-authored synthetic holdout, not an independent or production
accuracy estimate.

## External reviewer holdout

`holdout_template.csv` is intentionally header-only. No external cases or
reviewers have been recorded. It is separate from both
`frozen_holdout_v1.csv` and the 16-case regression suite.

The supplied reviewer files have been normalized into
`independent_holdout_v1.csv`: 19 cases from three pseudonymous authors across
all nine supported categories. The file is ready for the freeze check, but it
is not yet reported as independent validation because the dataset, classifier,
and evaluator must be committed and tagged together before scoring.

Each independent case uses this schema:

| Field | Requirement |
|---|---|
| `dataset_version` | One version shared by every case, such as `independent-v1` |
| `id` | Unique pseudonymous case identifier |
| `evidence_json` | Non-empty JSON array of `{reference, observation}` objects |
| `missing_rows` | Integer when known; otherwise blank |
| `expected_rows`, `actual_rows` | Provide both together or leave both blank |
| `expected` | Ground-truth classifier category; blank labels are reported, not scored |
| `expected_findings_json` | Non-empty JSON string array when `expected` is present |
| `expected_uncertainty` | `candidate_only` or `unresolved` when labelled |
| `author_id` | Pseudonymous reviewer identifier |
| `reviewer_provenance` | Must be exactly `external-reviewer` |

Illustrative syntax only—this is not a recorded reviewer case:

```text
evidence_json=[{"reference":"LOG-EXAMPLE","observation":"Example evidence"}]
expected_findings_json=["Example expected finding"]
```

Scoring is fixed before evaluation: an exact category match receives credit;
partial category matches receive no credit. Expected findings and uncertainty
are reported separately. Missing labels are excluded from accuracy, and an
`unclassified` prediction remains unresolved rather than being promoted to a
cause.

1. Give the blank template to two or three external reviewers without showing
   them the classifier rules.
2. Add 15 to 20 cases. Use two or three pseudonymous `author_id` values and
   preserve each evidence reference in `evidence_json`. Set `expected_rows`
   and `actual_rows` together, or leave both empty.
3. Choose one expected category: `timeout`, `schema_mismatch`,
   `dependency_failure`, `early_termination`, `incomplete_data`,
   `delayed_run`, `duplicate_data`, `conflicting_evidence`, or `unclassified`.
4. Commit the completed CSV, `app/investigator.py`, and
   `scripts/evaluate_holdout.py` without running the evaluator. Tag that exact
   commit, for example `independent-holdout-v1`. The evaluator rejects changes
   to the dataset, classifier, or scoring implementation after this freeze.
5. Run `make independent-holdout FILE=evaluation/independent_holdout_v1.csv REF=independent-holdout-v1`.
6. Publish the pseudonymized cases, JSON result, Markdown report, tag, and a
   short description of the independent authorship process. The report records
   dataset, evaluator, scoring-rule, and classifier-configuration versions; UTC
   evaluation time; hashes; completed and missing labels; exact matches;
   incorrect findings; unresolved predictions; input-evidence traceability; and
   the no-causation-claim contract.

OpsIntel AI does not claim an independent accuracy result until an external
evaluator supplies and runs those unseen cases.

## Human impact study

The impact study is separate from both classifier evaluations. Its ten cases,
hidden key, counterbalanced P1–P4 assignment, and blank 40-trial measurement
worksheet are versioned here. Each trial has a stable ID and records duration,
diagnosis, evidence references, confidence, unsafe confirmation, LLM state, and
any protocol deviation. Follow `reports/impact-study-protocol.md`; if a separate
database setup is approved, load the cases with `make impact-study-database`.
Summarize a copied results worksheet with:

```bash
make impact FILE=/absolute/path/to/completed-impact-results.csv \
  RECRUITMENT=/absolute/path/to/recruitment.md
```

The command also accepts the blank template and produces a pending result with
explicit missing trials and no comparison. No time-saving result is claimed
until real participants complete every frozen assignment and the comparison
checks pass. Keep the key hidden and keep `OPSINTEL_LLM_ENABLED=false` so this
study measures only the deterministic OpsIntel workflow.
