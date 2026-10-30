# OpsIntel demonstration script

This script describes the **intended live rehearsal**, not an already verified recording. The current repository has no measured memory benchmark or participant study. Use only a disposable Exasol Personal deployment and source-backed incident evidence. Never invent a causal source to make the confirmation step succeed.

## Preparation

1. Run backend and frontend checks. Start an authorized Exasol Personal deployment, initialize the demo schema if safe, and apply the additive memory migration.
2. Configure separate investigator and reviewer bearer grants in a local secret manager. Keep tokens out of the screen recording.
3. Confirm that the chosen incident has real causal evidence meeting the approved cause-specific checklist. The existing synthetic seed logs alone may be insufficient; if so, demonstrate the `needs_more_evidence` decision instead of a false confirmation.
4. Rehearse the exact browser and SQL steps. Capture source IDs and timestamps without displaying credentials or sensitive logs.

## Walkthrough

1. **Detect:** open the dashboard and show an Exasol-sourced failed run. State clearly that the bundled incident telemetry is synthetic demonstration data.
2. **Investigate:** select the run, inspect log/source references, row-count comparison, extracted signals, and any dependency correlation. Point out where the classifier abstains or shows competing symptoms.
3. **Explain:** show candidate explanations and the separate unconfirmed cause field. A candidate and a similarity score do not prove causation.
4. **Submit:** with an investigator grant, enter a specific hypothesis and attach source-backed symptom and causal evidence. The result is pending.
5. **Review:** with a different authorized reviewer grant, inspect every cited source and complete the versioned cause-specific checklist. Approve only if all gates pass and contradictions are resolved. Otherwise choose needs more evidence or reject.
6. **Remember:** after a valid approval, show the active record and audit event in Exasol. Show the `CONFIRMED_INCIDENTS`, `INCIDENT_FEATURES`, and `INCIDENT_AUDIT` tables, without revealing tokens.
7. **Retrieve:** investigate a later, different run. Show a historical candidate with matching/differing features, version, date, and the required engineer-verification label. Reject a false candidate if appropriate. A new run remains unconfirmed until its own review.
8. **Analyse:** open the public-data scorecard and memory operational counts. State that public labels are project mappings and that memory accuracy, learning curve, and human time savings remain unmeasured until independently adjudicated cases and participants exist.

If Exasol is unavailable, show the public scorecard and repository SQL/code path, and explicitly say the persistence demonstration could not be verified. The previous three-minute submission video is a historical draft and must be re-recorded before claiming it demonstrates verified memory.
