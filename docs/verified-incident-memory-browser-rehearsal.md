# Verified Incident Memory browser rehearsal checklist

Use this checklist with a real, authorized reviewer and source-backed evidence. Test tokens and the email demo gate are not human reviewer identity. Do not use the prior `e2e-*` actor records as human approval.

## Before the rehearsal

- [ ] Exasol health is green; note Exasol version, database schema and migration status.
- [ ] Investigator and authorized reviewer sign in with separate real identities and roles.
- [ ] The reviewer is explicitly authorized under the project policy; record their identity through the normal application audit path.
- [ ] Select one real incident with source evidence for both the symptom and proposed cause. Record source URL, retrieval date, exact evidence reference, and the label's provenance.
- [ ] Capture the active confirmed-memory count and matching SQL audit baseline. Do not edit or use frozen evaluator cases.

## Browser workflow

- [ ] **Submit:** Investigator opens the incident, reviews its logs/structured evidence, submits a cause hypothesis, and sees `pending`. Confirm no root cause is presented as confirmed.
- [ ] **Review:** Reviewer opens the exact pending packet, examines symptom and causal references, checks every versioned criterion and alternatives/conflicts, and records a rationale. Missing or contradictory evidence must prevent approval.
- [ ] **Confirm:** Reviewer approves only if policy criteria are satisfied. Capture reviewer identity, decision, timestamp, checklist, evidence references, and audit ID. Verify the submitter cannot self-approve.
- [ ] **Persist:** Query Exasol read-only and verify one submission, one active confirmation, one confirmation audit, and evidence references equal the reviewed packet.
- [ ] **Restart:** Restart only the application process (not the database). Reopen the incident and verify the same reviewer, status, cause description, and evidence references.
- [ ] **Retrieve:** Open a differently worded, independently evidenced incident with the same underlying cause. Verify the candidate cites the confirmed incident's evidence and is labelled a candidate requiring engineer verification.
- [ ] **Stale match:** Correct or revoke a confirmed memory through the authorized workflow. Verify affected prior matches become `stale` and the revoked record is excluded from new retrieval.
- [ ] **Revocation audit:** Reopen the history and verify the reviewer, rationale, timestamp, before/after snapshots, and one revocation audit. Ensure the original confirmation history remains traceable.

## Rehearsal evidence and stop conditions

- [ ] Save timestamped screenshots or a screen recording only with permission from all participants; redact credentials and sensitive source data.
- [ ] Save sanitized API logs, read-only SQL output, run IDs, incident IDs, reviewer identity, and app/database restart details.
- [ ] Record any latency only as a measured observation with hardware, Exasol version, history size, repetitions, and cache state.
- [ ] Stop and mark the rehearsal incomplete if reviewer identity cannot be established, source evidence is not traceable, a required criterion is missing, a contradictory signal remains, persistence differs after restart, or a revoked match is still offered as active.

A successful browser rehearsal verifies workflow usability for that session. It is not a participant study, causal-accuracy estimate, or independent classifier evaluation.
