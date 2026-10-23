# Project roadmap

This roadmap separates engineering work from evidence that must come from
people or services outside the project team. Pending work must not be presented
as a completed result.

## Contribution-sized work

- Add licensed public failure-log samples with source URL, licence, immutable
  revision, expected outcome, and published classifier errors.
- Add more exported orchestrator formats through the existing normalization
  boundary.
- Improve accessible loading, empty, unknown, conflicting, and disconnected
  states without adding dashboard clutter.
- Add a repeatable concurrency benchmark only when a representative workload
  and safe test database are available.

## External validation

- Have two or three external authors freeze 15-20 unseen holdout cases before
  scoring them.
- Run the prepared counterbalanced investigation study with at least three
  participants and publish mixed or negative results as well as positive ones.
- Execute and record the optional LLM grounding evaluation with an authorized
  API account. The configured model remains account-dependent even though
  `gpt-6-luna` is listed in the official model catalog.

## Service-dependent exploration

- Evaluate Exasol Text AI only when the target Exasol Personal deployment
  exposes the required capability and its data-handling constraints are known.
- Add an MCP evidence-query surface only when a concrete judge or operator
  workflow requires agent access. It must expose read-only evidence queries,
  preserve source references, and never confirm or repair a pipeline.

## Deliberate non-goals

- Automatic remediation.
- Confidence percentages without calibration data.
- Production, concurrency, or cost claims inferred from the local sequential
  benchmark.
