# Final demo approach

## The story

Show one engineering question from start to finish: **what failed, which evidence supports that description, what remains uncertain, and what would be required before a cause enters shared memory?** Keep the sequence visible: observation → candidate → authorized review → persisted memory → later candidate. The investigator proposes; the reviewer decides. A later similarity match never confirms a new incident.

The supplied four-page feature plan is useful for this narrative and for the confirm-then-retrieve shape. Treat its 21% starting figure as historical context only. Do not use its illustrative learning curve, target accuracy, “every confirmation makes the team faster” claim, or proposed in-database matching as project results: those are not supported by current evidence and do not describe the implementation.

## Before recording

1. Use an authorized, disposable Exasol Personal deployment. Check the database, API, and dashboard before recording; do not reset any database that may contain data.
2. Use real, distinct investigator and authorized reviewer identities. Do not show temporary `e2e-*` test identities as people or use test records as human approval.
3. Choose source-backed evidence for both the symptom and proposed cause. Review the approved class-specific criteria, missing information, alternatives, and contradictions before recording. If any required gate fails, demonstrate `needs_more_evidence` instead of approving.
4. Prepare a later, differently worded incident with independently traceable evidence. Never use the frozen 19-case reviewer holdout as demo or tuning material.
5. Prepare a read-only SQL query for the submission, confirmation, and audit records. Have the application restart command ready; restart the app only, not Exasol.
6. Hide tokens, passwords, personal tabs, unrelated notifications, and sensitive log content. Capture only evidence you have permission to show.
7. Test the exact route, source references, and window arrangement once. Record a clean take; do not edit in simulated clicks, confirmations, SQL output, or metrics.

## Three-minute recording plan

| Time | Show | Say / do |
|---|---|---|
| 0:00–0:18 | Dashboard and a failed run | “Pipeline incidents scatter status, counts, and logs. OpsIntel brings those observations together so an engineer can inspect the evidence behind the next diagnostic step.” |
| 0:18–0:42 | Actual Exasol query and result | Point to the query that calculates completeness/history or dependency paths. Say the bundled pipeline history is synthetic demo telemetry. Describe downstream links as time-correlated, not proven causes. |
| 0:42–1:08 | Selected investigation | Open a run, inspect its row-count comparison, source references, and extracted signals. State the supported symptom, then show any missing evidence or conflict. Do not call a candidate a root cause. |
| 1:08–1:35 | Investigator submission | Submit a specific hypothesis with its source evidence. Show the pending state and explain that the submitter cannot approve it. |
| 1:35–2:00 | Separate reviewer view | The authorized reviewer reads the cited source, records a rationale, and checks the required criteria. Approve only when every criterion is supported and no disqualifying conflict remains. Otherwise select `needs_more_evidence` or reject. |
| 2:00–2:22 | Exasol audit query, then app restart | Show the real reviewer identity, decision, timestamp, evidence references, and one audit event. Restart the application and show that the record remains. Never imply a test token is a human reviewer. |
| 2:22–2:42 | Differently worded later incident | Show the retrieved historical incident with cited matching and differing evidence. Say similarity ranks a candidate; it is not a probability, and the new run stays unconfirmed. |
| 2:42–3:00 | Evaluation limits / closing | “The public issue comparison uses project-assigned labels, and the 19-case reviewer result is small and unchanged. We have not measured engineer time savings or an independent memory learning curve. OpsIntel keeps the evidence and decision visible.” |

## If the live memory workflow cannot be demonstrated

The latest local execution report says Exasol is unavailable in that environment. Do not record the sequence above as completed until the database and real reviewer workflow are available. Record an honest product walkthrough instead: show the dashboard, a source-linked investigation, the actual SQL/code path, and the unavailable-service state. Say directly that persistence, human review, restart, and retrieval were not demonstrated in that recording. Label that video a **product walkthrough**, not a verified-memory end-to-end demo.

The prior Exasol exercise used temporary test identities and was revoked afterward. It established an earlier technical test of persistence and retrieval, but it is not a real human decision and must not be presented as one. There is no measured learning curve, independent memory accuracy, human time saving, or new video recording yet.

## Q&A approach

- **Why Exasol?** Show the actual window and dependency SQL plus persistent memory/audit tables. Be candid that Python computes fingerprint similarity and local benchmarks did not show an Exasol speed advantage.
- **How do you avoid invented causes?** Separate observed facts, candidates, and confirmed causes. Show citations and the reviewer checklist; the automated classifier and optional LLM cannot approve.
- **Does memory improve accuracy or save time?** We do not yet have an independently adjudicated chronological memory set or a participant study, so no such improvement is claimed.
- **What is synthetic?** The seeded pipeline history is synthetic. Public issue excerpts are separate and their labels are project-assigned unless the corpus record says otherwise.
- **What happens when evidence conflicts?** The system surfaces the conflict and leaves the cause unconfirmed; the reviewer must resolve it or request more evidence.
