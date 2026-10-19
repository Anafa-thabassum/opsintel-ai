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

`holdout_template.csv` remains empty so an external reviewer can test evidence
classification without sharing cases with the project team in advance.

1. Copy `holdout_template.csv` outside the repository.
2. Add at least 20 cases. Put each case's log messages in `logs_json` as a JSON
   array, for example `["Execution deadline exceeded"]`. Set `expected_rows`
   and `actual_rows` together, or leave both empty when row totals are not part
   of the case.
3. Choose one expected category: `timeout`, `schema_mismatch`,
   `dependency_failure`, `early_termination`, `incomplete_data`,
   `delayed_run`, `duplicate_data`, `conflicting_evidence`, or `unclassified`.
4. Freeze the current commit before revealing the file.
5. Run `python -m scripts.evaluate_holdout /path/to/holdout.csv`.
6. Preserve the raw file, commit SHA, output, and evaluator name.

OpsIntel AI does not claim an independent accuracy result until an external
evaluator supplies and runs those unseen cases.
