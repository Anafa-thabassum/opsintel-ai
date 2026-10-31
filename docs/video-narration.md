# Verified Incident Memory video narration — recording draft

**Target runtime:** 2:45–3:00, including the actual browser and SQL actions. This script is not a transcript of the existing MP4. Record the memory sections only after an authorized Exasol deployment and real, separate investigator/reviewer identities are available. Follow the [demo approach](demo-script.md). If a cause does not satisfy the approved criteria, show `needs_more_evidence`; never stage an approval.

## Spoken script and screen cues

### 0:00–0:20 — The problem

**Screen:** Dashboard, then open a failed run.

**Say:** “When a data pipeline fails, engineers often have to piece together run status, row counts, and logs. OpsIntel brings those observations into one investigation and keeps the evidence attached to each finding.”

### 0:20–0:45 — What Exasol does

**Screen:** Show the real query and its result; point to completeness/history or the dependency path.

**Say:** “Exasol calculates completeness, rolling run history, and time-correlated downstream paths. The pipeline records here are synthetic demo telemetry. A downstream failure after an upstream one is a correlation to inspect, not proof of causation.”

### 0:45–1:10 — Evidence before explanation

**Screen:** Show the selected incident, source references, row comparison, extracted signals, and any evidence gap.

**Say:** “For this run, these are the observed facts. OpsIntel reports the supported symptom and shows what evidence is missing. A candidate explanation is only a possibility; the system leaves the root cause unconfirmed.”

### 1:10–1:35 — Investigator submission

**Screen:** With the investigator identity, submit a hypothesis and its source references; show the pending state.

**Say:** “An investigator can propose a specific cause with traceable supporting evidence. Submission creates a review request. The investigator cannot approve their own hypothesis.”

### 1:35–2:00 — Authorized review

**Screen:** Switch to the different authorized reviewer, inspect cited evidence and the actual versioned criteria; record the rationale and decision.

**Say:** “A separate authorized reviewer checks the source evidence, the class-specific criteria, and any alternatives or contradictions. Missing or conflicting support means more evidence is needed. Only a review that passes every required gate can create a confirmed memory.”

### 2:00–2:20 — Persistence

**Screen:** Run a read-only Exasol query showing the real confirmation and audit row, then restart the application process and reopen the record.

**Say:** “Exasol stores the reviewed record and audit history. After restarting the application, the reviewer, decision, timestamp, and evidence references are still present.”

### 2:20–2:40 — Retrieval stays a candidate

**Screen:** Investigate a differently worded later run with the same cause; show the cited historical candidate and matching/differing features.

**Say:** “This later incident uses different wording. OpsIntel retrieves a similar confirmed incident and shows the evidence on both sides. FastAPI computes the similarity score; it is a retrieval signal, not a probability. The new incident remains unconfirmed until it is reviewed on its own evidence.”

### 2:40–3:00 — Honest close

**Screen:** Briefly show the evaluation/limitations summary.

**Say:** “Current CI reports 200 passing automated tests. Our public issue comparison uses project-assigned labels, and the frozen reviewer set is small. We have no independent memory learning curve or measured engineer time savings. OpsIntel is designed to make the evidence and the human decision inspectable.”

## Fallback narration when Exasol or an authorized reviewer is unavailable

Do not use the preceding memory-workflow narration. Record only the dashboard, an investigation, and the actual SQL or code path. Say: “This is a product walkthrough. Exasol-backed confirmation, persistence after restart, and later retrieval were not available to verify in this recording, so I’m not presenting them as completed here.” Do not show seeded, test-only approvals as human decisions. See the full stop conditions in the [demo approach](demo-script.md).
