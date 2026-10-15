
import json
from pathlib import Path

import pyexasol


def get_connection():
    secrets_path = (
        Path.home()
        / ".exasol/personal/deployments/default/secrets.json"
    )

    if not secrets_path.exists():
        raise FileNotFoundError(
            f"Exasol credentials not found: {secrets_path}"
        )

    secrets = json.loads(secrets_path.read_text())
    password = secrets["dbPassword"]

    return pyexasol.connect(
        dsn="127.0.0.1:8563",
        user="sys",
        password=password,
        websocket_sslopt={"cert_reqs": 0},
    )


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
