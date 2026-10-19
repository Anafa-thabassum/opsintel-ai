"""Load the frozen impact-study cases into an initialized OPSINTEL schema."""

import csv
from pathlib import Path

from app.db import get_connection


CASES = Path(__file__).resolve().parents[1] / "evaluation/impact_cases_v1.csv"


def main():
    with CASES.open(newline="") as source:
        cases = list(csv.DictReader(source))

    connection = get_connection()
    try:
        for case in cases:
            parameters = {
                **case,
                "run_id": int(case["run_id"]),
                "expected_rows": int(case["expected_rows"]),
                "actual_rows": int(case["actual_rows"]),
            }
            connection.execute(
                """
                INSERT INTO OPSINTEL.PIPELINE_RUNS
                VALUES (
                    {run_id!d}, {pipeline_name}, {status},
                    {expected_rows!d}, {actual_rows!d}, CURRENT_TIMESTAMP
                )
                """,
                parameters,
            )
            connection.execute(
                """
                INSERT INTO OPSINTEL.PIPELINE_LOGS
                VALUES (
                    {run_id!d}, {run_id!d}, {log_level},
                    {log_message}, CURRENT_TIMESTAMP
                )
                """,
                parameters,
            )
    finally:
        connection.close()

    print(f"Loaded {len(cases)} frozen impact-study cases.")


if __name__ == "__main__":
    main()
