# ExaThon submission checklist

## Eligibility

- [ ] Team contains one to three members.
- [x] Exasol Personal is the data platform.
- [x] Only synthetic data is included.
- [ ] Confirm all work complies with the challenge-window rule.
- [x] Repository uses an OSI-approved MIT licence.

## Required submission assets

- [x] Clear problem statement and target user.
- [ ] Review, commit, and push the final working-tree changes.
- [x] Clean README with setup, usage, deployment, and run guide.
- [x] Reproducible tests and evaluation report.
- [x] Pitch deck PDF and PPTX show 133/133 and label the 120-minute cascade as
      temporal correlation, with causation unconfirmed.
- [ ] Re-record the demo from `submission/video-narration.txt`; the existing
      2:34 MP4 predates the final cascade, test count, and LLM grounding changes.
- [ ] Upload the deck and video and add publicly accessible links.

## Before the deadline

- [x] Run backend tests, evaluation, frontend lint, and production build.
- [x] Run the Exasol benchmark and preserve its raw result.
- [x] Historical isolated clean-clone rehearsal completed at revision
      `2a17d4f`; dependency installation, automated checks, API startup, and
      frontend startup passed, while the Exasol-backed workflow was blocked.
- [ ] After publishing, repeat the final clean-clone check on the submitted
      revision and use only an authorized disposable Exasol database for any
      database-backed rehearsal.
- [ ] Check every repository, deck, and video link in a private browser window.
- [ ] Remove secrets, personal tabs, and local paths from public artifacts.
- [ ] Update the GitHub description so it does not claim automated recovery.
- [ ] Add repository topics: `exasol`, `data-engineering`, `incident-response`,
      `fastapi`, `react`, and `hackathon`.
- [ ] Submit before **25 October 2026 at 11:59 PM IST**.

## Finalist preparation

- [ ] Rehearse the 15-minute presentation with a working live demo.
- [ ] Prepare a recorded-demo fallback.
- [ ] Rehearse the five-minute Q&A using `docs/judge-qa.md`.
- [ ] Keep Exasol, the API, and the dashboard running before the session starts.
