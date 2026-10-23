# Submission package

| File | Purpose |
|---|---|
| `opsintel-ai-pitch-deck.pdf` | Primary pitch deck for upload |
| `opsintel-ai-pitch-deck.pptx` | Editable pitch deck for the live presentation |
| `opsintel-ai-demo.mp4` | Existing 2:34 narrated draft; re-record from the current build before submission |
| `video-narration.txt` | Final 11-scene narration with current test and evaluation claims |

The narration reflects the expanded incident suite, failed-run comparison,
137-test suite, and claim-level LLM grounding. The current PPTX and PDF include
the 137/137 result and describe the 120-minute cascade as temporal correlation
with causation unconfirmed. The committed MP4 was recorded before those final
changes, so **do not submit it unchanged**. Re-record
`video-narration.txt` in the team's own voice from the current build. If the
recording includes a live Exasol workflow, use only an explicitly authorized
disposable database. Keep the result below three minutes and then run:

```bash
make submission-check
```

Before submission, upload the video to an accessible location and test the
link in a private browser window. GitHub may display or download the MP4, but a
public video host is usually easier for judges.
