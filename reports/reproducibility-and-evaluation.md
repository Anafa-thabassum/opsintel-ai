# Reproducibility and evaluation record

**Updated:** 2026-10-31  
**Scope:** Current repository commands, frozen evaluation references, project-labelled checks, and measured local Exasol evidence. This report is an index; frozen source datasets and their original reports are not rewritten here.

## Reproduce the project

From a clean checkout with Python 3.12+ (CI uses 3.12), Node 20.19+ or 22.12+, and a configured Exasol Personal service:

```bash
make setup
# Start Exasol Personal separately, then configure backend environment.
make database
make memory-migrate
make api
```

In another terminal, run `cd frontend && npm ci && npm run dev`. The API's `/health` endpoint verifies DB connectivity. See [Quickstart](../docs/QUICKSTART.md) for exact environment setup.

Routine checks (no Exasol required):

```bash
make verify
```

`make verify` runs pytest, the synthetic challenge, Oxlint, and Vite production build. The latest recorded local run on 2026-10-31 reported **200 tests passed**, **16/16** challenge cases, lint passed, and build passed with a non-failing bundle-size advisory. A previous completed run reported **198 tests**; the two-count difference is from subsequently added benchmark utility tests. These are test-suite counts, not classifier accuracy. CI workflow definitions are in `.github/workflows/ci.yml`.

Evaluation commands and intent:

| Command | Dataset / effect | Interpretation |
|---|---|---|
| `python -m tests.run_evaluation` | 16 predefined challenge cases | Synthetic regression challenge; 16/16 in the latest recorded run. |
| `make holdout` | `evaluation/frozen_holdout_v1.csv` | Project-authored synthetic holdout; 27/27, not independent. Writes output to stdout. |
| `make independent-holdout FILE=... REF=...` | A separately frozen reviewer dataset | Do not run against the existing hidden labels for tuning. Current published result is the historical 4/19. |
| `make public-evaluate` | Public V1 compatibility CSV | Project-assigned labels; 6/9 historical result. |
| `make public-evaluate-v2` | Public issue V2 CSV | Project-assigned taxonomy mapping; 7/10. Regenerates reports; review the diff before accepting changes. |
| `make exasol-proof` | Existing `OPSINTEL` tables/views | Read-only Exasol demonstration query. |
| `make benchmark` | New `OPSINTEL_BENCHMARK` synthetic workload | Creates/imports an isolated benchmark schema and drops it by default. Run only against a designated benchmark deployment. |
| `make benchmark-compare` | Synthetic 1M/10M Exasol and DuckDB workload | Writes a new JSON report and SVG chart; local single-user latency comparison. |
| `python -m scripts.benchmark_memory_exasol --run-id <id> ...` | Existing active, reviewer-confirmed memories | Read-only; current results only cover zero active history. No confirmation fixtures are generated. |

## Keep evaluation sets separate

| Evaluation | Result | Label/input provenance | Hash / source |
|---|---:|---|---|
| Predefined challenge | 16/16 | Synthetic, built for regression | Invoked by `tests.run_evaluation`; not a production estimate. |
| Frozen project-authored holdout | 27/27 | Synthetic, project-authored | CSV SHA-256: `a7da47b53b8b985238cfb4f59cfb71755a3b76a283467df125c99e46fa181f71`; result and classifier metadata in `reports/frozen-holdout-v1.md`. |
| Frozen reviewer holdout | 4/19 (21.1%) | 19 synthetic cases from three pseudonymous reviewer authors; frozen as `independent-holdout-v1` | CSV SHA-256: `64d766d4782ee94223796e91d79c35fb359d3dcd9de414b1b8ebed41afacf71`; frozen evaluator SHA-256: `c07b1f2ddcc3b5e1f11447bf8f7aa98501c2f99c5d8f3657106945254d9feb75`; details in `reports/independent-holdout-v1.md`. |
| Public V1 | 6/9 | Project-labelled framework-generated compatibility messages | CSV SHA-256: `294a9a0f765c910229483cd520a294efb91a72f92a625d74b77151d1a5f42482`; `reports/public-corpus-v1.md`. |
| Public V2 | 7/10 | Project-assigned mapping from issue labels/evidence to supported categories | CSV SHA-256: `3542452c1994da590d04ebd34e42cb207d8e4555c1e641dbfa6ba70badbd41df`; `reports/public-corpus-v2.md`. |
| Public development corpus V1 | No independent score claimed here | Provenance-tracked development records | JSONL SHA-256: `f2937bf8f842f61a77432c41a61351d7d70b4c314e70e4d212fc118a1dcfaf58`. |
| Public development corpus V2 | Development only | Provenance-tracked public issue records; not an independent test set | JSONL SHA-256: `2b16264d2954e57f9202dc3d9fa2e00e04d466598748caeb31e158381c331a5e`; see `reports/corpus-validation-v2.md`. |

The frozen 19-case holdout, historical 4/19 report, source labels, hashes, and evaluator are unchanged. Never use its hidden labels for classifier or threshold tuning. The 27/27 set was authored within the project and entered history with its result; repository history does not prove labels were frozen before scoring. The public issue sets use project labels, not independent adjudication. Public issue text can have different licensing from repository source code; the source manifest records uncertainty.

## Analytical benchmark methodology and results

`make benchmark` invokes `scripts/benchmark_exasol.py`, which imports deterministic synthetic pipeline history, calculates window features, runs a daily aggregation query, disables Exasol query cache, performs one warm-up and repeated timed fetches (seven repetitions by default), then drops only its dedicated `OPSINTEL_BENCHMARK` schema unless `--keep-schema` is set. The recorded 1M run: 20 pipelines, 5% failure rate, 3.025 s import, 7 repetitions, median 473.209 ms, nearest-rank p95 503.947 ms. Raw samples are in `reports/exasol-benchmark.json`.

`make benchmark-compare` uses seven queries per engine at 1M and 10M synthetic rows, sequentially on the same local machine. Exasol's query cache is disabled; DuckDB uses a reused in-memory connection. Recorded medians:

| Rows | Exasol Personal | DuckDB 1.5.6 |
|---:|---:|---:|
| 1,000,000 | 437.118 ms | 114.912 ms |
| 10,000,000 | 4,902.269 ms | 1,080.358 ms |

Environment recorded in benchmark JSON: Python 3.14.0, macOS 26.6.2 arm64. These historical records do not include host model/physical RAM or Exasol VM CPU/RAM/DBMS version for the analytical comparison; those fields must remain “not captured.” Results are local single-user query timings, not production, throughput, concurrency, or cost claims. DuckDB was faster in both recorded sizes; no Exasol speed advantage is claimed.

## Verified Incident Memory measurement

The Exasol-backed end-to-end demonstration used two test telemetry rows sourced from Apache Airflow issue #36734 and temporary test identity tokens. The reviewer actor was `e2e-reviewer-test-b`; its confirmation was revoked after rehearsal. There is no active human-reviewed memory record. See `reports/exasol-memory-e2e-2026-10-31.md` for the exact evidence and audits.

The only memory-latency measurement used zero active history and one revoked row excluded from retrieval. With 3 warm-ups and 30 repetitions, `similar_incidents(record=False)` returned unresolved/zero candidates; median was 51.627 ms and p95 64.753 ms. Python traced peak was 349,780 bytes and process peak RSS 51,363,840 bytes. Exasol server memory and query-cache mode were not measured or independently verified. This is an empty-history baseline, not a scale curve or accuracy result. Protocol: `reports/exasol-memory-benchmark-protocol-v1.md`.

## Human validation and remaining limits

- Participant study: **0/40 assigned trials, 0/4 participants** recorded; no time-saving or benefit claim.
- Authorized reviewer: **no real human approval found** in the local memory audit; the test-only approval is revoked.
- Increasing-history retrieval: unmeasured because active reviewer-confirmed records do not exist.
- Live LLM grounding and account entitlement: unverified; mocked tests are not live evidence.
- New public candidate cases in `reports/public-independent-incident-candidates-v1.md` were not added to datasets or evaluated, and were not checked against hidden holdout labels.
- Full clean-clone reproduction of the current repository, including live Exasol and browser memory flow: **not completed**. A historical clean-checkout rehearsal exists for an earlier revision and is not claimed as current full reproduction.
