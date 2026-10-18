# Independent holdout evaluation

This folder lets a reviewer test evidence classification without sharing cases
with the project team in advance.

1. Copy `holdout_template.csv` outside the repository.
2. Add at least 20 cases. Put each case's log messages in `logs_json` as a JSON
   array, for example `["Execution deadline exceeded"]`.
3. Choose one expected category: `timeout`, `schema_mismatch`,
   `dependency_failure`, `early_termination`, `incomplete_data`, or
   `unclassified`.
4. Freeze the current commit before revealing the file.
5. Run `python -m scripts.evaluate_holdout /path/to/holdout.csv`.
6. Preserve the raw file, commit SHA, output, and evaluator name.

The empty template is intentional. OpsIntel AI does not claim an independent
accuracy result until an external evaluator supplies and runs unseen cases.
