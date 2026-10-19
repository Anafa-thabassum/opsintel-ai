
import json
import os
import ssl
from pathlib import Path

import pyexasol


CASCADE_WINDOW_MINUTES = 120


def get_connection():
    """Create an Exasol connection from environment or local Personal secrets."""
    password = os.getenv("EXASOL_PASSWORD")

    if not password:
        secrets_path = Path(
            os.getenv(
                "EXASOL_SECRETS_PATH",
                Path.home()
                / ".exasol/personal/deployments/default/secrets.json",
            )
        ).expanduser()

        if not secrets_path.exists():
            raise FileNotFoundError(
                "Set EXASOL_PASSWORD or provide Exasol Personal credentials at "
                f"{secrets_path}"
            )

        password = json.loads(secrets_path.read_text())["dbPassword"]

    verify_tls = os.getenv("EXASOL_TLS_VERIFY", "false").lower() == "true"

    return pyexasol.connect(
        dsn=os.getenv("EXASOL_DSN", "127.0.0.1:8563"),
        user=os.getenv("EXASOL_USER", "sys"),
        password=password,
        websocket_sslopt={
            "cert_reqs": ssl.CERT_REQUIRED if verify_tls else ssl.CERT_NONE
        },
    )


def check_connection():
    connection = get_connection()

    try:
        connection.execute("SELECT 1 FROM DUAL").fetchone()
    finally:
        connection.close()


def get_failed_pipelines():
    connection = get_connection()

    try:
        result = connection.execute("""
            SELECT
                RUN_ID,
                PIPELINE_NAME,
                EXPECTED_ROWS,
                ACTUAL_ROWS,
                MISSING_ROWS,
                RUN_STATUS,
                EXCESS_ROWS
            FROM OPSINTEL.PIPELINE_HEALTH_FEATURES
            WHERE IS_INCIDENT = 1
            ORDER BY RUN_ID
        """)

        return result.fetchall()
    finally:
        connection.close()


def get_pipeline_trend():
    """Return daily incident telemetry calculated by Exasol."""
    connection = get_connection()

    try:
        result = connection.execute("""
            SELECT
                TO_CHAR(RUN_TIME, 'YYYY-MM-DD') AS RUN_DAY,
                COUNT(*) AS TOTAL_RUNS,
                SUM(
                    IS_INCIDENT
                ) AS INCIDENT_COUNT,
                ROUND(AVG(COMPLETENESS_PCT), 1) AS AVG_COMPLETENESS_PCT,
                ROUND(AVG(ROLLING_FAILURE_RATE_PCT), 1)
                    AS AVG_ROLLING_FAILURE_RATE_PCT
            FROM OPSINTEL.PIPELINE_HEALTH_FEATURES
            GROUP BY TO_CHAR(RUN_TIME, 'YYYY-MM-DD')
            ORDER BY RUN_DAY
        """)

        return result.fetchall()
    finally:
        connection.close()


def get_failure_cascades():
    """Return time-ordered upstream/downstream failure correlations."""
    connection = get_connection()

    try:
        result = connection.execute(f"""
            WITH LATEST_FAILED AS (
                SELECT
                    RUN_ID,
                    PIPELINE_NAME,
                    RUN_TIME,
                    ROW_NUMBER() OVER (
                        PARTITION BY PIPELINE_NAME
                        ORDER BY RUN_TIME DESC, RUN_ID DESC
                    ) AS RECENCY_RANK
                FROM OPSINTEL.PIPELINE_RUNS
                WHERE RUN_STATUS = 'FAILED'
            )
            SELECT
                dependency_path.ROOT_PIPELINE,
                upstream.RUN_ID AS ROOT_RUN_ID,
                TO_CHAR(upstream.RUN_TIME, 'YYYY-MM-DD HH24:MI:SS')
                    AS ROOT_RUN_TIME,
                dependency_path.DOWNSTREAM_PIPELINE,
                downstream.RUN_ID AS DOWNSTREAM_RUN_ID,
                TO_CHAR(downstream.RUN_TIME, 'YYYY-MM-DD HH24:MI:SS')
                    AS DOWNSTREAM_RUN_TIME,
                dependency_path.DEPENDENCY_DEPTH,
                dependency_path.DEPENDENCY_PATH,
                ROUND(
                    MINUTES_BETWEEN(downstream.RUN_TIME, upstream.RUN_TIME),
                    2
                ) AS CORRELATION_LAG_MINUTES
            FROM OPSINTEL.PIPELINE_DEPENDENCY_CASCADE dependency_path
            JOIN LATEST_FAILED upstream
              ON upstream.PIPELINE_NAME = dependency_path.ROOT_PIPELINE
             AND upstream.RECENCY_RANK = 1
            JOIN LATEST_FAILED downstream
              ON downstream.PIPELINE_NAME = dependency_path.DOWNSTREAM_PIPELINE
             AND downstream.RECENCY_RANK = 1
            WHERE MINUTES_BETWEEN(
                      downstream.RUN_TIME,
                      upstream.RUN_TIME
                  ) > 0
              AND MINUTES_BETWEEN(
                      downstream.RUN_TIME,
                      upstream.RUN_TIME
                  ) <= {CASCADE_WINDOW_MINUTES}
            ORDER BY upstream.RUN_ID,
                     dependency_path.DEPENDENCY_DEPTH,
                     downstream.RUN_ID
        """)
        return [
            row for row in result.fetchall()
            if 0 < float(row[8]) <= CASCADE_WINDOW_MINUTES
        ]
    finally:
        connection.close()
