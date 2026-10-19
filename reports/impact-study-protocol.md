# OpsIntel AI human-impact study protocol

**Status: ready to administer; no participant study has been conducted.**

## Objective and boundary

Evaluate whether OpsIntel AI helps people reach a defensible first diagnosis
on synthetic pipeline incidents more quickly while preserving correctness,
evidence traceability, uncertainty, and safe handling of unverified causes.

This is a four-participant, 40-trial counterbalanced convenience study. It can
describe results for this sample; it cannot establish causal or production
impact. The optional LLM must remain disabled with
`OPSINTEL_LLM_ENABLED=false` for every trial.

## Frozen materials

| File | Purpose |
|---|---|
| `evaluation/impact_cases_v1.csv` | Ten participant-visible synthetic incidents |
| `evaluation/impact_case_key_v1.csv` | Facilitator-only ground-truth categories |
| `evaluation/impact_assignments_v1.csv` | Trial IDs, order, case, and condition for P1–P4 |
| `evaluation/impact_template.csv` | Blank measurement worksheet for all 40 trials |
| `evaluation/impact_recruitment_template.md` | Minimal pseudonymous recruitment record |

Freeze the tested commit before the first participant. Do not edit these v1
files after data collection starts. Use participant codes only; do not collect
names, employers, contact details, or other identifying information.

## Task and participant instructions

Each participant investigates ten incidents. For every incident, submit:

1. one diagnosis category;
2. the evidence record references supporting that choice;
3. confidence from 1–5; and
4. whether any unverified candidate was treated as a confirmed cause.

Use this prompt unchanged in both conditions:

> Investigate the displayed incident and stop when you can submit one category:
> timeout, schema mismatch, dependency failure, early termination, incomplete
> data, or unresolved. Cite the run or log records supporting your choice, rate
> confidence from 1–5, and do not present a possible cause as confirmed.

Do not tell participants that OpsIntel should be faster or more accurate.

## Ground truth and success criteria

The facilitator-only key defines one expected evidence category for each case.
The analyzer derives correctness; participants must not see the key or receive
correctness feedback between trials.

A trial is:

- **correct** when the submitted category equals the frozen key;
- **incorrect** when it names a different category;
- **unresolved** when the participant explicitly abstains; and
- **traceable** when at least one concrete run or log reference is recorded.

The predefined study target requires all 40 assigned trials plus:

- assisted median time at least 30% lower than the manual median;
- assisted correctness no lower than manual correctness;
- at least 90% assisted evidence traceability; and
- zero assisted unsafe-confirmation events.

No partial, pending, or unbalanced dataset may support a time-saving claim.

## Assignment and order control

- Four participants each complete ten trials: five `manual` and five
  `opsintel`.
- Each participant sees each case once, preventing within-person repeated-case
  learning.
- Every case appears twice in each condition across the four participants.
- P1 and P2 begin with `manual`; P3 and P4 begin with `opsintel`.
- Conditions alternate within each participant, and case orders differ between
  participants to reduce systematic order and learning effects.
- Follow the frozen order and use the same computer and timer procedure where
  practical.

Counterbalancing reduces obvious order bias but does not remove all learning,
facilitator, or participant-experience effects.

## CSV capture schema

| Field | Rule |
|---|---|
| `trial_id` | Frozen unique identifier such as `P1-T01` |
| `participant_id` | Pseudonymous code `P1`–`P4` |
| `trial_order` | Frozen positive order within participant |
| `case_id` | Frozen synthetic incident ID |
| `condition` | `manual` or `opsintel` |
| `seconds` | Positive elapsed seconds from evidence display to submission |
| `diagnosis` | One allowed category or `unresolved` |
| `evidence_references` | Semicolon-separated run/log references; blank means untraceable |
| `confidence` | Integer 1–5 |
| `unsafe_confirmation` | `true` only if an unverified candidate was presented as confirmed |
| `llm_enabled` | Must remain `false` |
| `protocol_deviation` | Brief non-identifying note; blank when none |

Blank measurement fields mean a pending trial. Partially filled measurement
fields are reported as incomplete. Neither contributes to comparative results.

## Facilitator procedure

1. Record the frozen Git commit and confirm `OPSINTEL_LLM_ENABLED=false`.
2. Start the deterministic application with the frozen synthetic cases. Database
   setup is a separate, explicit operation; do not reset a populated database.
3. Copy `evaluation/impact_template.csv` to a private results file.
4. Assign the next unused participant code and read the standard prompt.
5. For `manual`, show only the assigned raw incident evidence. For `opsintel`,
   show the corresponding dashboard investigation. Never show the key.
6. Start timing when evidence becomes visible. Stop when all required participant
   responses are submitted.
7. Record the response verbatim using evidence IDs, not personal information.
   Record interruptions or departures from the procedure in
   `protocol_deviation`; do not silently remove trials.
8. After data capture, complete the recruitment record and run:

   ```bash
   make impact \
     FILE=/absolute/path/to/completed-impact-results.csv \
     RECRUITMENT=/absolute/path/to/recruitment.md
   ```

The same command can analyze the blank template: it produces a pending report
with zero completed trials and no comparison or improvement claim.

## Measures and analysis

| Measure | Definition |
|---|---|
| Investigation duration | Seconds from evidence visibility to complete response |
| Correctness | Submitted category compared with the frozen key |
| Evidence traceability | At least one cited run/log reference |
| Unresolved outcome | Explicit `unresolved` diagnosis |
| Unsafe certainty | Unverified candidate presented as confirmed |
| Protocol deviation | Recorded departure from the standardized procedure |

When—and only when—all assigned trials are complete, the analyzer reports each
condition's median duration, category correctness, traceability, confidence,
unresolved outcomes, and unsafe-confirmation events. It records input hashes,
the tested commit, missing data, deviations, and limitations. Calculations are
descriptive; no inferential or causal claim is made from four participants.

## Current results

| Metric | Manual | OpsIntel AI | Difference |
|---|---:|---:|---:|
| Completed trials | 0 | 0 | Pending |
| Median investigation duration | Pending | Pending | Pending |
| Correctness | Pending | Pending | Pending |
| Evidence traceability | Pending | Pending | Pending |
| Unresolved outcomes | Pending | Pending | Pending |
| Unsafe-confirmation events | Pending | Pending | Pending |

No genuine participants, observations, or time savings have been recorded.
