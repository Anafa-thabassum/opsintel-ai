"""Normalize Airflow or dbt JSON exports and optionally load them into Exasol."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from app.db import get_connection


def _timestamp(value):
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed.strftime("%Y-%m-%d %H:%M:%S")


def _status(value):
    return "SUCCESS" if str(value).lower() in {"success", "passed", "pass"} else "FAILED"


def normalize_airflow(payload):
    runs = []
    for item in payload.get("dag_runs", []):
        logs = item.get("logs") or [f"Airflow DAG run state: {item.get('state', 'unknown')}"]
        runs.append({
            "run_id": int(item["opsintel_run_id"]),
            "pipeline_name": item["dag_id"],
            "status": _status(item.get("state")),
            "expected_rows": int(item.get("expected_rows", 0)),
            "actual_rows": int(item.get("actual_rows", 0)),
            "run_time": _timestamp(item["end_date"]),
            "logs": [str(log) for log in logs],
            "source": "airflow",
        })
    return runs


def normalize_dbt(payload):
    generated_at = payload.get("metadata", {}).get("generated_at")
    runs = []
    for item in payload.get("results", []):
        opsintel = item.get("opsintel", {})
        rows_affected = item.get("adapter_response", {}).get("rows_affected", 0)
        runs.append({
            "run_id": int(opsintel["run_id"]),
            "pipeline_name": item["unique_id"],
            "status": _status(item.get("status")),
            "expected_rows": int(opsintel.get("expected_rows", rows_affected or 0)),
            "actual_rows": int(rows_affected or 0),
            "run_time": _timestamp(item.get("completed_at") or generated_at),
            "logs": [str(item.get("message") or f"dbt node status: {item.get('status', 'unknown')}")],
            "source": "dbt",
        })
    return runs


def normalize_export(kind, payload):
    if kind == "airflow":
        return normalize_airflow(payload)
    if kind == "dbt":
        return normalize_dbt(payload)
    raise ValueError(f"Unsupported orchestrator format: {kind}")


def load_into_exasol(runs):
    connection = get_connection()
    try:
        next_log_id = int(connection.execute(
            "SELECT COALESCE(MAX(LOG_ID), 0) FROM OPSINTEL.PIPELINE_LOGS"
        ).fetchone()[0]) + 1
        for run in runs:
            connection.execute(
                """
                INSERT INTO OPSINTEL.PIPELINE_RUNS VALUES (
                    {run_id!d}, {pipeline_name}, {status},
                    {expected_rows!d}, {actual_rows!d},
                    TO_TIMESTAMP({run_time}, 'YYYY-MM-DD HH24:MI:SS')
                )
                """,
                run,
            )
            for message in run["logs"]:
                connection.execute(
                    """
                    INSERT INTO OPSINTEL.PIPELINE_LOGS VALUES (
                        {log_id!d}, {run_id!d}, {level}, {message},
                        TO_TIMESTAMP({run_time}, 'YYYY-MM-DD HH24:MI:SS')
                    )
                    """,
                    {
                        **run,
                        "log_id": next_log_id,
                        "level": "INFO" if run["status"] == "SUCCESS" else "ERROR",
                        "message": message,
                    },
                )
                next_log_id += 1
    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=("airflow", "dbt"))
    parser.add_argument("path", type=Path)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="insert normalized records into the configured OPSINTEL schema",
    )
    args = parser.parse_args()
    runs = normalize_export(args.kind, json.loads(args.path.read_text()))
    if args.apply:
        load_into_exasol(runs)
        print(f"Loaded {len(runs)} {args.kind} run(s) into Exasol.")
    else:
        print(json.dumps(runs, indent=2))


if __name__ == "__main__":
    main()
