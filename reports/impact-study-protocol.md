# OpsIntel AI impact study protocol

## Question

Does OpsIntel AI reduce the time required for a data engineer to reach a
defensible first diagnosis while preserving evidence traceability?

## Participants and cases

- Recruit at least three people with data engineering or analytics experience.
- Use at least ten synthetic incidents that are not in the implementation's
  predefined challenge set.
- Randomize the order of incidents for each participant.
- Compare two conditions: raw tables and logs, then the OpsIntel AI dashboard.
- Do not change the classifier after the case set is revealed.

## Measures

Record these values for every participant, incident, and condition:

| Measure | Definition |
|---|---|
| Time to first diagnosis | Seconds from opening the evidence to submitting a category |
| Diagnosis agreement | Whether the submitted category matches the hidden case label |
| Evidence traceability | Whether the participant cites at least one supporting source record |
| Confidence | Participant rating from 1 to 5 |
| Unsafe certainty | Whether an unverified candidate is presented as confirmed |

Copy `evaluation/impact_template.csv` outside the repository and record one row
for each participant, case, and condition. Allowed outcomes are `correct`,
`incorrect`, and `unresolved`; boolean fields must be `true` or `false`.

Summarize the completed file without manually calculating results:

```bash
make impact FILE=/path/to/impact-results.csv
```

Preserve the raw CSV, generated JSON, exact commit, participant count, and any
excluded trials together. The script reports measurements; it does not decide
whether the study design is externally valid.

## Success thresholds

The prototype meets the study target only if all conditions hold:

- median time to first diagnosis improves by at least 30%;
- diagnosis agreement does not decrease;
- at least 90% of OpsIntel-assisted responses cite source evidence;
- zero assisted responses convert an unverified candidate into a confirmed
  root cause.

## Results table

Complete this table only after the study. Preserve raw timings separately.

| Metric | Raw evidence | OpsIntel AI | Difference |
|---|---:|---:|---:|
| Median diagnosis time (seconds) | Pending | Pending | Pending |
| Diagnosis agreement | Pending | Pending | Pending |
| Evidence traceability | Pending | Pending | Pending |
| Unsafe certainty events | Pending | Pending | Pending |

## Reporting rule

Do not replace `Pending` values with estimates. Report participant count, case
count, raw results, exclusions, and the exact commit used.
