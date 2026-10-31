# Verified Incident Memory Exasol benchmark protocol v1

**Status:** Protocol is ready; a populated-history scale curve is blocked until actual, authorized reviewer confirmations exist.  
**Integrity rule:** Do not create, clone, relabel, or promote incidents to active memory to fill benchmark sizes. Do not use frozen evaluator cases or hidden labels. This protocol reads only records already confirmed through the authorized reviewer workflow.

## Question and scope

Measure how Exasol-backed retrieval latency and application memory change as the count of distinct active, reviewer-confirmed incident records grows. This is a systems benchmark, not a classifier accuracy estimate, independent evaluation, or human study.

The benchmark runner `scripts/benchmark_memory_exasol.py` calls the existing investigation and `similar_incidents(..., record=False)` paths. It does not write match records or memory decisions. `--expected-history` makes each run fail if the observed active-memory count differs from the declared size. The query run must be real source-backed evidence and must not be the same run as any historical memory candidate.

## Data and size plan

Use only distinct incident records that were submitted and approved by an authorized reviewer through the normal API. Preserve original evidence references, reviewer ID, decision timestamps, cause description, checklist, and audit rows. A public example with an OpsIntel-assigned category is not a confirmed memory record until a real reviewer performs the required review. No benchmark fixture may impersonate a reviewer.

Target checkpoints: **1, 5, 10, 25, 50, 100, 250, and 500 active records**. Run at a checkpoint only when exactly that number of eligible records exists. If the active count skips a checkpoint, mark it unavailable rather than copy or fabricate rows. The application currently scans at most 500 recent active candidates; the 500-record point is the configured retrieval ceiling, not a claim about larger database histories.

Use the same fixed source-backed query run for all checkpoints, record its provenance, and pre-register the expected relevant incident ID or expected no-match result before measuring. A query used for checking a match must not be part of that history. Keep the source corpus, active incident IDs, and match expectation in the run manifest. If the history does not include independently confirmed examples, correctness can only be structural (stable result, self-exclusion, active status, and evidence references); do not report semantic recall or precision.

## Procedure

For every available exact-size checkpoint:

1. Record host, OS/architecture, physical memory, Exasol Personal launcher and DBMS versions, VM CPU/RAM allocation, Python version, repository revision and dirty state, fingerprint version, similarity threshold, and query-cache configuration. Never record secrets.
2. Run read-only SQL to capture active/revoked counts and a digest of the incident IDs and evidence-reference metadata. Do not export sensitive evidence excerpts into the public report.
3. Run `scripts/benchmark_memory_exasol.py --run-id <query-run> --expected-history <N> --warmups 5 --repetitions 50`. For a pre-registered known match, add `--expected-match <incident-id>`. The script's defaults are 3 warm-ups and 30 measured repetitions; use the larger values for a reportable checkpoint.
4. Preserve each JSON result and the exact command. Run checkpoints in ascending order and repeat the entire sequence once, recording each sequence separately. Do not combine samples across restarts or cache conditions.
5. Report min, median, nearest-rank p95, max, all samples, result count, candidate count, and correctness condition. Report Python `tracemalloc` peak and process peak RSS with units. Exasol server memory must be collected from an authoritative Exasol metric if available; Python memory is not a substitute.
6. Run a separate cold-cache pass only if Exasol query-cache control is explicitly applied and its state is verified. Label the normal pass with the observed cache mode; never call an uncontrolled pass “cold.”
7. Confirm afterward that submission, confirmation, audit, and match row counts did not change. The runner uses `record=False`; if they do change, invalidate the run and investigate before retrying.

## Acceptance and reporting

A checkpoint passes the runner's mechanical checks only when: active memory count equals N; results are stable throughout warm-ups and repetitions; the query run is excluded; returned records are active and have evidence references; and the selected result agrees with the pre-registered expected match when one is supplied. A no-ground-truth run is labelled structural-only.

Publish each checkpoint separately with raw JSON. Performance improvement requires a comparable earlier run on the same host, Exasol build, memory allocation, query/cache policy, query, and benchmark data. Until such comparable measurements exist, report only observed timings and do not claim improvement.

## Current measured baseline (2026-10-31)

Only the **zero-active-history** case was available, so this is an empty-history smoke benchmark, not the requested increasing-history curve. The sole confirmed row is revoked and excluded from retrieval. See the exact samples in `reports/exasol-memory-e2e-2026-10-31.md`.
