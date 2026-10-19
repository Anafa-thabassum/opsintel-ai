"""Print live Exasol history and evidence results for the demo incident."""

import json

from app.db import get_connection


def fetch_proof(run_id=1, pipeline_name="daily_sales_import"):
    connection = get_connection()
    try:
        history = connection.execute(
            """
            SELECT
                RUN_ID,
                RUN_STATUS,
                EXPECTED_ROWS,
                ACTUAL_ROWS,
                MISSING_ROWS,
                COMPLETENESS_PCT,
                PREVIOUS_STATUS,
                ROLLING_AVG_ACTUAL_ROWS,
                ROLLING_FAILURE_RATE_PCT,
                TO_CHAR(RUN_TIME, 'YYYY-MM-DD HH24:MI:SS')
            FROM OPSINTEL.PIPELINE_HEALTH_FEATURES
            WHERE PIPELINE_NAME = {pipeline_name}
            ORDER BY RUN_TIME DESC, RUN_ID DESC
            """,
            {"pipeline_name": pipeline_name},
        ).fetchall()
        evidence = connection.execute(
            """
            SELECT DISTINCT
                r.RUN_ID,
                r.PIPELINE_NAME,
                r.RUN_STATUS,
                r.EXPECTED_ROWS,
                r.ACTUAL_ROWS,
                l.LOG_ID,
                l.LOG_LEVEL,
                l.LOG_MESSAGE,
                TO_CHAR(l.LOG_TIME, 'YYYY-MM-DD HH24:MI:SS')
            FROM OPSINTEL.PIPELINE_RUNS r
            JOIN OPSINTEL.PIPELINE_LOGS l ON r.RUN_ID = l.RUN_ID
            WHERE r.RUN_ID = {run_id!d}
            ORDER BY l.LOG_ID
            """,
            {"run_id": int(run_id)},
        ).fetchall()
    finally:
        connection.close()

    return {
        "source": "live Exasol query",
        "pipeline_name": pipeline_name,
        "run_id": int(run_id),
        "historical_completeness_columns": [
            "run_id",
            "status",
            "expected_rows",
            "actual_rows",
            "missing_rows",
            "completeness_pct",
            "previous_status",
            "rolling_avg_actual_rows",
            "rolling_failure_rate_pct",
            "run_time",
        ],
        "historical_completeness_rows": [list(row) for row in history],
        "evidence_columns": [
            "run_id",
            "pipeline_name",
            "status",
            "expected_rows",
            "actual_rows",
            "log_id",
            "log_level",
            "log_message",
            "log_time",
        ],
        "evidence_rows": [list(row) for row in evidence],
    }


def main():
    print(json.dumps(fetch_proof(), indent=2, default=str))


if __name__ == "__main__":
    main()
