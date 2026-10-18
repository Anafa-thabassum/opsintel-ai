
import json
import os
import ssl
from pathlib import Path

import pyexasol


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
                EXPECTED_ROWS - ACTUAL_ROWS AS MISSING_ROWS,
                RUN_STATUS
            FROM OPSINTEL.PIPELINE_RUNS
            WHERE EXPECTED_ROWS > ACTUAL_ROWS
               OR RUN_STATUS = 'FAILED'
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
                    CASE
                        WHEN RUN_STATUS = 'FAILED'
                          OR EXPECTED_ROWS > ACTUAL_ROWS
                        THEN 1
                        ELSE 0
                    END
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
