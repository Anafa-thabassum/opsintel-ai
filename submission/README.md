# Submission package

> **Problem statement:** Data engineers lose time diagnosing failed pipelines because run metadata, row counts, and logs are fragmented; they need one traceable investigation that identifies the next diagnostic action without treating an unverified cause as fact.

OpsIntel combines clearly labelled synthetic Exasol telemetry with a separate
public Airflow/dbt issue workspace. The public ten-case category comparison is
7/10 against project-authored labels; it is not independent validation.

| File | Purpose |
|---|---|
| `opsintel-ai-pitch-deck.pdf` | Updated 11-slide pitch deck |
| `opsintel-ai-pitch-deck.pptx` | Editable source deck |
| `opsintel-ai-demo.mp4` | Historical 2:34 recording; it does not show verified memory |
| `video-narration.txt` | Draft for a future recording; not a recording transcript |

The updated deck describes investigator submission, separate reviewer
approval, Exasol audit storage, application-side similarity ranking, public-data
limitations, and the actual validation boundary. It reports 200 passing tests
from the current CI run, 16/16 predefined synthetic challenge cases, and the 7/10
project-label comparison. It does not describe the 15/19 comparison as
independent validation.

The new memory walkthrough cannot be recorded on this machine today: the
Exasol service is unavailable, so no real confirmation, restart persistence,
or retrieval was demonstrated. Record it only with an authorized disposable
Exasol database, separate investigator/reviewer identities, and verified
source evidence. If the cause checklist cannot be satisfied, record a
`needs_more_evidence` outcome instead of a confirmation. Keep the video under
three minutes. The approved recording sequence and unavailable-service
fallback are in [the demo approach](../docs/demo-script.md); narration is in
`video-narration.txt`. Run `make submission-check` after the final recording is
added.
