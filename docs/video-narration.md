# Video narration draft for a verified-memory rehearsal

“OpsIntel investigates data pipeline failures from Exasol run history, logs, counts, and dependency records. The deterministic classifier reports supported symptoms and leaves ambiguous cases unresolved. It never confirms a cause.

An engineer can submit a causal hypothesis with source references. A separate authorized reviewer inspects the evidence and completes cause-specific verification checks. Only a passing review writes a confirmed incident to Exasol, together with an audit event. If evidence is missing or contradictory, the cause stays unconfirmed.

When a later run resembles a verified incident, OpsIntel retrieves that history as a candidate. It shows matching and differing features and requires a new engineer verification. Similarity is a retrieval score, not a probability that the diagnosis is correct.

Exasol calculates rolling pipeline health features and dependency paths, stores verified memory and audit history, and filters active historical candidates. The application calculates explainable token-pair similarity. The bundled pipeline telemetry is synthetic demonstration data. A separate public investigation mode searches locally cached Apache Airflow and dbt issues, showing original URLs, screened excerpts, category assessments and unresolved cases. Its project labels are unreviewed and do not measure independent accuracy. No measured time saving or fresh independent memory accuracy is claimed.”

Use this narration only after the live Exasol workflow in [the demo script](demo-script.md) has been rehearsed successfully. Otherwise present the missing integration honestly. The previously committed submission video and narration remain historical artifacts.
