"""Compare the OpsIntel analytical workload on Exasol and DuckDB."""

import argparse
import html
import json
import math
import platform
import statistics
from pathlib import Path
from time import perf_counter

import duckdb

from scripts.benchmark_exasol import benchmark as benchmark_exasol
from scripts.benchmark_exasol import percentile


DUCKDB_QUERY = """
    SELECT
        STRFTIME(RUN_TIME, '%Y-%m-%d') AS RUN_DAY,
        COUNT(*) AS TOTAL_RUNS,
        SUM(CASE WHEN RUN_STATUS = 'FAILED' THEN 1 ELSE 0 END) AS INCIDENTS,
        ROUND(AVG(COMPLETENESS_PCT), 2) AS AVG_COMPLETENESS_PCT,
        ROUND(AVG(ROLLING_FAILURE_RATE_PCT), 2) AS FAILURE_RATE_PCT
    FROM PIPELINE_FEATURES
    GROUP BY STRFTIME(RUN_TIME, '%Y-%m-%d')
    ORDER BY RUN_DAY
"""


def benchmark_duckdb(rows, repetitions):
    connection = duckdb.connect(":memory:")
    try:
        import_started = perf_counter()
        connection.execute(f"""
            CREATE TABLE PIPELINE_RUNS AS
            SELECT
                i AS RUN_ID,
                PRINTF('pipeline_%02d', i % 20) AS PIPELINE_NAME,
                CASE WHEN i % 20 = 0 THEN 'FAILED' ELSE 'SUCCESS' END
                    AS RUN_STATUS,
                1000 + i % 200 AS EXPECTED_ROWS,
                CASE
                    WHEN i % 20 = 0 THEN 1000 + i % 200 - (i % 100 + 1)
                    ELSE 1000 + i % 200
                END AS ACTUAL_ROWS,
                TIMESTAMP '2026-07-01' + i * INTERVAL '1 minute' AS RUN_TIME
            FROM RANGE(1, {int(rows) + 1}) AS generated(i)
        """)
        import_seconds = perf_counter() - import_started
        connection.execute("""
            CREATE VIEW PIPELINE_FEATURES AS
            SELECT
                *,
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
            FROM PIPELINE_RUNS
        """)
        connection.execute(DUCKDB_QUERY).fetchall()
        timings_ms = []
        result_days = 0
        for _ in range(repetitions):
            started = perf_counter()
            result_days = len(connection.execute(DUCKDB_QUERY).fetchall())
            timings_ms.append((perf_counter() - started) * 1000)

        return {
            "engine": "DuckDB",
            "version": duckdb.__version__,
            "rows": rows,
            "result_days": result_days,
            "repetitions": repetitions,
            "load_seconds": round(import_seconds, 3),
            "query_latency_ms": {
                "minimum": round(min(timings_ms), 3),
                "median": round(statistics.median(timings_ms), 3),
                "p95_nearest_rank": round(percentile(timings_ms, 0.95), 3),
                "maximum": round(max(timings_ms), 3),
                "samples": [round(value, 3) for value in timings_ms],
            },
        }
    finally:
        connection.close()


def run_comparison(row_counts, repetitions, engines):
    results = []
    for rows in row_counts:
        if "exasol" in engines:
            result = benchmark_exasol(rows, repetitions)
            results.append({
                "engine": "Exasol Personal",
                "rows": rows,
                "result_days": result["result_days"],
                "repetitions": repetitions,
                "load_seconds": result["import_seconds"],
                "query_latency_ms": result["query_latency_ms"],
            })
        if "duckdb" in engines:
            results.append(benchmark_duckdb(rows, repetitions))

    return {
        "benchmark": "OpsIntel window analytics and daily aggregation",
        "dataset": "identical deterministic synthetic pipeline history",
        "row_counts": row_counts,
        "repetitions": repetitions,
        "execution": "sequential local single-user runs",
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "scope": (
            "A local engine comparison, not a production throughput, "
            "concurrency, cost, or deployment benchmark."
            if len(engines) == 2
            else "Single-engine baseline only; run both engines under the same "
            "conditions before claiming a database comparison."
        ),
        "results": results,
    }


def render_svg(result, path):
    """Render an editable, dependency-free chart from recorded benchmark data."""
    rows = result["row_counts"]
    engines = sorted({item["engine"] for item in result["results"]})
    indexed = {
        (item["rows"], item["engine"]): item["query_latency_ms"]["median"]
        for item in result["results"]
    }
    values = [value for value in indexed.values() if value > 0]
    if not values:
        raise ValueError("Benchmark result contains no positive median latencies")
    minimum = max(1, min(values) / 1.5)
    maximum = max(values) * 1.35
    log_min, log_max = math.log10(minimum), math.log10(maximum)
    colors = ["#9b8cff", "#58ddb0", "#61d9f7"]
    width, height = 960, 540
    left, top, plot_width, plot_height = 100, 95, 790, 330
    group_width = plot_width / max(1, len(rows))
    bar_width = min(92, group_width / (len(engines) + 1))

    def y_position(value):
        ratio = (math.log10(value) - log_min) / (log_max - log_min)
        return top + plot_height * (1 - ratio)

    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 960 540">',
        '<rect width="960" height="540" fill="#090c14"/>',
        '<text x="48" y="46" fill="#f0f3fa" font-family="Arial" font-size="27" font-weight="700">Median analytical-query latency</text>',
        '<text x="48" y="72" fill="#9aa5bd" font-family="Arial" font-size="14">Identical deterministic workload · local single-user · milliseconds on a logarithmic scale</text>',
    ]
    for tick in (10, 100, 1000, 10000):
        if minimum <= tick <= maximum:
            y = y_position(tick)
            lines.extend([
                f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_width}" y2="{y:.1f}" stroke="#273149" stroke-width="1"/>',
                f'<text x="{left - 14}" y="{y + 5:.1f}" text-anchor="end" fill="#74809a" font-family="Arial" font-size="13">{tick:,}</text>',
            ])
    for row_index, row_count in enumerate(rows):
        group_center = left + group_width * (row_index + 0.5)
        for engine_index, engine in enumerate(engines):
            value = indexed.get((row_count, engine))
            if value is None:
                continue
            x = group_center - (len(engines) * bar_width) / 2 + engine_index * bar_width
            y = y_position(value)
            bar_height = top + plot_height - y
            color = colors[engine_index % len(colors)]
            lines.extend([
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width - 12:.1f}" height="{bar_height:.1f}" rx="8" fill="{color}"/>',
                f'<text x="{x + (bar_width - 12) / 2:.1f}" y="{y - 10:.1f}" text-anchor="middle" fill="#f0f3fa" font-family="Arial" font-size="13" font-weight="700">{value:,.1f} ms</text>',
            ])
        label = f"{row_count / 1_000_000:g}M rows"
        lines.append(f'<text x="{group_center:.1f}" y="456" text-anchor="middle" fill="#d7deef" font-family="Arial" font-size="15">{label}</text>')
    legend_x = 100
    for index, engine in enumerate(engines):
        color = colors[index % len(colors)]
        safe_engine = html.escape(engine)
        lines.extend([
            f'<rect x="{legend_x}" y="486" width="14" height="14" rx="3" fill="{color}"/>',
            f'<text x="{legend_x + 22}" y="498" fill="#9aa5bd" font-family="Arial" font-size="14">{safe_engine}</text>',
        ])
        legend_x += 180
    lines.append('</svg>')
    path.write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, nargs="+", default=[1_000_000, 10_000_000])
    parser.add_argument("--repetitions", type=int, default=7)
    parser.add_argument(
        "--engine",
        choices=("both", "exasol", "duckdb"),
        default="both",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--chart", type=Path)
    args = parser.parse_args()
    engines = {"exasol", "duckdb"} if args.engine == "both" else {args.engine}
    result = run_comparison(args.rows, args.repetitions, engines)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered)
    if args.chart:
        render_svg(result, args.chart)
    print(rendered, end="")


if __name__ == "__main__":
    main()
