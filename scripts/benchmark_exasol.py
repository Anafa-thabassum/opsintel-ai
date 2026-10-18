"""Run a reproducible synthetic analytics benchmark against Exasol."""

import argparse
import json
import math
import platform
import statistics
from datetime import datetime, timedelta
from time import perf_counter

from app.db import get_connection


SCHEMA = "OPSINTEL_BENCHMARK"
ANALYTICS_QUERY = f"""
    SELECT
        TO_CHAR(RUN_TIME, 'YYYY-MM-DD') AS RUN_DAY,
        COUNT(*) AS TOTAL_RUNS,
        SUM(CASE WHEN RUN_STATUS = 'FAILED' THEN 1 ELSE 0 END) AS INCIDENTS,
        ROUND(AVG(COMPLETENESS_PCT), 2) AS AVG_COMPLETENESS_PCT,
        ROUND(AVG(ROLLING_FAILURE_RATE_PCT), 2) AS FAILURE_RATE_PCT
    FROM {SCHEMA}.PIPELINE_FEATURES
    GROUP BY TO_CHAR(RUN_TIME, 'YYYY-MM-DD')
    ORDER BY RUN_DAY
"""


def make_rows(total, start=None):
    """Yield deterministic synthetic pipeline history."""
    start = start or datetime(2026, 7, 1)

    for run_id in range(1, total + 1):
        failed = run_id % 20 == 0
        expected = 1_000 + run_id % 200
        actual = expected - (run_id % 100 + 1) if failed else expected
        yield (
            run_id,
            f"pipeline_{run_id % 20:02d}",
            "FAILED" if failed else "SUCCESS",
            expected,
            actual,
            start + timedelta(minutes=run_id),
        )


def percentile(values, fraction):
    """Return the nearest-rank percentile used in the report."""
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * fraction) - 1)]


def benchmark(rows, repetitions, keep_schema=False):
    connection = get_connection()

    try:
        connection.execute(f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE")
        connection.execute(f"CREATE SCHEMA {SCHEMA}")
        connection.execute(f"""
            CREATE TABLE {SCHEMA}.PIPELINE_RUNS (
                RUN_ID DECIMAL(18,0),
                PIPELINE_NAME VARCHAR(100),
                RUN_STATUS VARCHAR(20),
                EXPECTED_ROWS DECIMAL(18,0),
                ACTUAL_ROWS DECIMAL(18,0),
                RUN_TIME TIMESTAMP
            )
        """)

        import_started = perf_counter()
        connection.import_from_iterable(
            make_rows(rows),
            (SCHEMA, "PIPELINE_RUNS"),
        )
        import_seconds = perf_counter() - import_started

        connection.execute(f"""
            CREATE VIEW {SCHEMA}.PIPELINE_FEATURES AS
            SELECT
                RUN_ID,
                PIPELINE_NAME,
                RUN_STATUS,
                EXPECTED_ROWS,
                ACTUAL_ROWS,
                RUN_TIME,
                ROUND(ACTUAL_ROWS * 100.0 / NULLIF(EXPECTED_ROWS, 0), 2)
                    AS COMPLETENESS_PCT,
                ROUND(
                    AVG(CASE WHEN RUN_STATUS = 'FAILED' THEN 1 ELSE 0 END)
                    OVER (
                        PARTITION BY PIPELINE_NAME
                        ORDER BY RUN_TIME
                        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
                    ) * 100,
                    2
                ) AS ROLLING_FAILURE_RATE_PCT
            FROM {SCHEMA}.PIPELINE_RUNS
        """)

        connection.execute(ANALYTICS_QUERY).fetchall()
        timings_ms = []
        result_days = 0

        for _ in range(repetitions):
            started = perf_counter()
            result_days = len(connection.execute(ANALYTICS_QUERY).fetchall())
            timings_ms.append((perf_counter() - started) * 1_000)

        return {
            "benchmark": "Exasol window analytics and daily aggregation",
            "dataset": "deterministic synthetic pipeline history",
            "rows": rows,
            "pipelines": 20,
            "incident_rate_pct": 5,
            "result_days": result_days,
            "repetitions": repetitions,
            "import_seconds": round(import_seconds, 3),
            "query_latency_ms": {
                "minimum": round(min(timings_ms), 3),
                "median": round(statistics.median(timings_ms), 3),
                "p95_nearest_rank": round(percentile(timings_ms, 0.95), 3),
                "maximum": round(max(timings_ms), 3),
                "samples": [round(value, 3) for value in timings_ms],
            },
            "environment": {
                "python": platform.python_version(),
                "platform": platform.platform(),
            },
            "scope": (
                "Local single-user benchmark; not a production throughput "
                "or concurrency claim."
            ),
        }
    finally:
        if not keep_schema:
            try:
                connection.execute(f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE")
            except Exception:
                pass
        connection.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=1_000_000)
    parser.add_argument("--repetitions", type=int, default=7)
    parser.add_argument(
        "--keep-schema",
        action="store_true",
        help=f"keep the isolated {SCHEMA} schema after the run",
    )
    args = parser.parse_args()

    if args.rows < 1 or args.repetitions < 1:
        parser.error("rows and repetitions must be positive")

    print(json.dumps(
        benchmark(args.rows, args.repetitions, args.keep_schema),
        indent=2,
    ))


if __name__ == "__main__":
    main()
