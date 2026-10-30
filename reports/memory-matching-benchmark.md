# Memory matching benchmark — pending live Exasol run

The matching implementation filters active non-self records in Exasol and computes bounded Jaccard plus structured-feature scores in Python. The additive migration and a rollback-only one-record SQL workflow passed against local Exasol Personal. No representative corpus or timed repeated workload was available, so retrieval latency, throughput, and database-side candidate query performance have not been measured. No speed claim is made.

For a reproducible benchmark, record the Exasol Personal version, hardware, table row counts, candidate counts, cold/warm cache state, query text, number of repetitions, median and tail latency, and the fingerprint version. Use real or explicitly licensed incident records. Do not present the existing synthetic Exasol–DuckDB workload as a verified-memory benchmark.
