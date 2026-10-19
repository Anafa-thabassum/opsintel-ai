# Submission package

| File | Purpose |
|---|---|
| `opsintel-ai-pitch-deck.pdf` | Primary pitch deck for upload |
| `opsintel-ai-pitch-deck.pptx` | Editable pitch deck for the live presentation |
| `opsintel-ai-demo.mp4` | Existing 2:34 narrated demo; re-record after the final Exasol reset |
| `video-narration.txt` | Final 11-scene narration with current test and evaluation claims |

The deck and narration now reflect the expanded incident suite, dependency
cascade, failed-run comparison, 132-test suite, and claim-level LLM grounding. The committed MP4 was
recorded before those final changes, so **do not submit it unchanged**. Reset
Exasol, rehearse the live flow, and re-record `video-narration.txt` in the
team's own voice. Keep the result below three minutes and then run:

```bash
make submission-check
```

Before submission, upload the video to an accessible location and test the
link in a private browser window. GitHub may display or download the MP4, but a
public video host is usually easier for judges.
