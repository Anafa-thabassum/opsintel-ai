# OpsIntel AI impact study protocol

**Status: ready to administer; no participant results recorded.**

## Question

Does OpsIntel AI reduce the time required for a data engineer to reach a
defensible first diagnosis while preserving evidence traceability?

This study measures the deterministic investigation experience. Run it with
`LLM_ENABLED=false`; independent LLM-summary quality is a separate evaluation.

## Frozen materials

| File | Purpose |
|---|---|
| `evaluation/impact_cases_v1.csv` | Ten participant-visible synthetic incidents |
| `evaluation/impact_case_key_v1.csv` | Facilitator-only expected categories |
| `evaluation/impact_assignments_v1.csv` | Frozen order and condition for P1–P4 |
| `evaluation/impact_template.csv` | Prefilled 40-trial results worksheet |

Do not change these v1 files after participant testing starts. Use pseudonymous
participant IDs only and do not collect names, employers, email addresses, or
other personal information.

## Design

- Recruit four adults with data engineering, analytics engineering, database,
  or pipeline-operations experience.
- Each participant investigates ten cases: five from raw evidence (`manual`)
  and five with the dashboard (`opsintel`).
- A participant sees each case only once, avoiding a repeated-case learning
  effect.
- Every case is seen twice in each condition across the four participants.
- Follow the frozen trial order; do not give correctness feedback between
  trials.
- Use the same computer and timer procedure for both conditions when possible.

This is a small counterbalanced convenience sample, not a controlled production
study. Participant recruitment must be reported honestly.

## Facilitator procedure

1. Freeze and record the tested Git commit. Start Exasol Personal.
2. Load the study data with `make impact-study-database`, then start the API and
   dashboard with `LLM_ENABLED=false`.
3. Copy the prefilled `evaluation/impact_template.csv` to a private results
   file.
4. Assign the participant the next unused slot from P1 through P4 and explain
   the five diagnosis choices plus `unresolved`.
5. For `manual`, show only the matching row from `impact_cases_v1.csv`. For
   `opsintel`, open the matching pipeline in the dashboard. Never show the key.
6. Start timing when the evidence is visible. Stop when the participant submits
   a diagnosis, supporting source reference, confidence from 1–5, and whether
   they treated an unverified candidate as confirmed.
7. Record the row exactly. Note technical interruptions separately and exclude
   a trial only with a written reason; rerun the full study design if a frozen
   assignment is removed.
8. After all 40 trials, run:

   ```bash
   make impact FILE=/absolute/path/to/completed-impact-results.csv
   ```

The command rejects incomplete, duplicate, reordered, or condition-swapped
trials; derives correctness from the frozen key; records file hashes and the Git
commit; and writes `reports/impact-study-v1.json`.

## Measures

| Measure | Definition |
|---|---|
| Time to first diagnosis | Seconds from evidence display to submission |
| Diagnosis agreement | Submitted category equals the frozen case label |
| Evidence traceability | A concrete source record is entered |
| Confidence | Participant rating from 1 to 5 |
| Unsafe certainty | An unverified candidate is presented as confirmed |

## Success thresholds

The study target is met only if all conditions hold:

- median time to first diagnosis improves by at least 30%;
- diagnosis agreement does not decrease;
- at least 90% of OpsIntel-assisted responses cite source evidence;
- zero assisted responses convert an unverified candidate into a confirmed
  root cause; and
- every design-balance check in the generated report passes.

## Results

| Metric | Raw evidence | OpsIntel AI | Difference |
|---|---:|---:|---:|
| Median diagnosis time (seconds) | Pending | Pending | Pending |
| Diagnosis agreement | Pending | Pending | Pending |
| Evidence traceability | Pending | Pending | Pending |
| Unsafe certainty events | Pending | Pending | Pending |

Do not replace `Pending` with estimates. Publish the pseudonymized raw CSV,
generated JSON, exclusions, participant recruitment description, and exact
commit together. Claim time saved only if the recorded result supports it.
