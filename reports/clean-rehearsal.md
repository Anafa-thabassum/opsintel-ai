# Clean-copy rehearsal

Date: 19 October 2026 (Asia/Kolkata)

## Result

A clean working copy of the current candidate was created outside the repository,
initialized as a fresh Git snapshot, and exercised using the documented commands.

| Check | Result |
|---|---:|
| Backend tests | 80/80 passed |
| Synthetic regression cases | 16/16 passed |
| Frontend lint | Passed |
| Frontend production build | Passed |
| PPTX slides | 11 |
| PDF pages | 11 |
| Existing MP4 duration | 154.445 seconds |

## Limitation

The sandbox could not reach the Python package index, so dependency installation
from an empty virtual environment was not completed. The code checks above reused
the repository's already-installed Python and Node dependencies while executing
the copied source. This is a clean-source rehearsal, **not** a full independent
clean-machine installation result.

The existing MP4 also predates the final dependency-cascade, 80-test, and
claim-level LLM changes. Its duration is valid, but it must be re-recorded from
`submission/video-narration.txt` before submission.

## Final external rehearsal

Run these commands on a machine with network access and Exasol Personal running:

```bash
git clone https://github.com/Anafa-thabassum/opsintel-ai.git
cd opsintel-ai
make setup
make database
make verify
make exasol-proof
make benchmark-compare
make submission-check
```

Then open the dashboard, complete the end-to-end demo flow, verify the refreshed
video is below three minutes, and compare every number in the README, reports,
deck, and narration before publishing.
