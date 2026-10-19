# Holdout evaluation

## Published frozen holdout

`frozen_holdout_v1.csv` contains 27 project-authored synthetic cases that are
separate from the 16-case regression suite. It covers all nine classifier
outcomes with three cases per expected category.

The labels were frozen before execution. The published report records the
dataset hash, classifier hash, classifier commit, category totals, and every
prediction:

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

`holdout_template.csv` remains empty so external reviewers can test evidence
classification without sharing cases with the project team in advance.

1. Give the blank template to two or three external reviewers without showing
   them the classifier rules.
2. Add 15 to 20 cases. Put each case's pseudonymous reviewer ID in `author_id`.
   Put each case's log messages in `logs_json` as a JSON
   array, for example `["Execution deadline exceeded"]`. Set `expected_rows`
   and `actual_rows` together, or leave both empty when row totals are not part
   of the case.
3. Choose one expected category: `timeout`, `schema_mismatch`,
   `dependency_failure`, `early_termination`, `incomplete_data`,
   `delayed_run`, `duplicate_data`, `conflicting_evidence`, or `unclassified`.
4. Commit the completed CSV and classifier without running the evaluator, then
   tag that commit, for example `independent-holdout-v1`.
5. Run `make independent-holdout FILE=evaluation/independent_holdout_v1.csv REF=independent-holdout-v1`.
6. Publish the pseudonymized cases, JSON result, Markdown error analysis, tag,
   and a short description of the independent authorship process.

OpsIntel AI does not claim an independent accuracy result until an external
evaluator supplies and runs those unseen cases.

## Human impact study

The impact study is separate from both classifier evaluations. Its ten cases,
hidden key, counterbalanced P1–P4 assignment, and prefilled results worksheet are
versioned here. Follow `reports/impact-study-protocol.md`; load the cases with
`make impact-study-database` and summarize all 40 completed trials with:

```bash
make impact FILE=/absolute/path/to/completed-impact-results.csv \
  RECRUITMENT=/absolute/path/to/recruitment.md
```

No time-saving result is claimed until real participants complete the frozen
assignment. Keep the key hidden during administration and run with the optional
LLM disabled so this study measures the deterministic OpsIntel workflow.
