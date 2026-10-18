
from app.db import get_failed_pipelines, get_connection


def classify_evidence(log_messages, missing_rows):
    """Classify evidence without claiming an unverified root cause."""
    text = " ".join(log_messages).lower()

    if any(word in text for word in ("timeout", "timed out", "time limit")):
        return (
            "timeout",
            "Logs report a timeout or execution time limit. "
            "The reason the pipeline exceeded the limit is not confirmed.",
            "Inspect execution duration, query plans, resource usage, "
            "and recent workload changes.",
        )

    if any(word in text for word in (
        "schema mismatch",
        "incompatible type",
        "data type",
        "does not match expected",
        "column type",
    )):
        return (
            "schema_mismatch",
            "Logs indicate a possible schema or data-type mismatch. "
            "The exact incompatible field should be verified.",
            "Compare the incoming schema with the target table definition "
            "and inspect the failing field.",
        )

    if any(word in text for word in (
        "dependency failure",
        "upstream task failed",
        "upstream dependency",
        "dependency failed",
    )):
        return (
            "dependency_failure",
            "Logs indicate an upstream dependency failure. "
            "The upstream task's failure should be investigated.",
            "Inspect the upstream task status, its logs, and dependency "
            "execution order.",
        )

    # Prefer a specific early-termination signal over a generic row-count issue.
    if "ended before all expected rows were processed" in text:
        return (
            "early_termination",
            "Logs report that processing ended before all expected rows "
            "were processed. The underlying reason is not confirmed.",
            "Inspect the execution logs around termination and identify "
            "the first reported error.",
        )

    if "source returned only" in text or missing_rows > 0:
        return (
            "incomplete_data",
            "The available data indicates that fewer rows were received "
            "than expected. The reason for the discrepancy is not confirmed.",
            "Compare source and target row counts, inspect source extracts, "
            "and check filtering or rejected-row logs.",
        )

    return (
        "unclassified",
        "The available evidence does not support a specific failure category.",
        "Inspect the complete pipeline logs and relevant source and target "
        "metrics.",
    )


def investigate_pipeline(run_id: int):
    """Gather pipeline metadata and logs to build an evidence-based investigation."""
    rows = get_failed_pipelines()

    incident = next(
        (row for row in rows if int(row[0]) == run_id),
        None,
    )

    if incident is None:
        return None

    connection = get_connection()

    try:
        result = connection.execute(
            """
            SELECT DISTINCT LOG_ID, LOG_LEVEL, LOG_MESSAGE
            FROM OPSINTEL.PIPELINE_LOGS
            WHERE RUN_ID = %d
            ORDER BY LOG_ID
            """ % int(run_id)
        )
        log_rows = result.fetchall()
    finally:
        connection.close()

    expected_rows = int(incident[2])
    actual_rows = int(incident[3])
    missing_rows = int(incident[4])
    log_messages = [str(log[2]) for log in log_rows]

    evidence = [
        {
            "type": "pipeline_status",
            "observation": f"Pipeline status is {incident[5]}",
            "source": "OPSINTEL.PIPELINE_RUNS",
        },
        {
            "type": "row_count",
            "observation": (
                f"Expected {expected_rows} rows, "
                f"but received {actual_rows}"
            ),
            "source": "OPSINTEL.PIPELINE_RUNS",
        },
    ]

    for log in log_rows:
        evidence.append({
            "type": "pipeline_log",
            "observation": f"[{log[1]}] {log[2]}",
            "source": "OPSINTEL.PIPELINE_LOGS",
            "log_id": int(log[0]),
        })

    category, hypothesis, recommended_action = classify_evidence(
        log_messages, missing_rows
    )

    return {
        "run_id": int(run_id),
        "pipeline_name": incident[1],
        "status": incident[5],
        "expected_rows": expected_rows,
        "actual_rows": actual_rows,
        "missing_rows": missing_rows,
        "category": category,
        "hypothesis": hypothesis,
        "confidence": "low",
        "recommended_action": recommended_action,
        "evidence": evidence,
        "limitations": [
            "The sample logs are synthetic test data.",
            "The underlying cause has not been confirmed.",
            "Recommendations are diagnostic suggestions, not executed repairs.",
        ],
    }


def assess_root_causes(incident):
    """Return evidence-supported candidates, never assert confirmation."""
    evidence = incident.get("evidence", [])
    evidence_text = " ".join(
        item.get("observation", "").lower()
        for item in evidence
    )

    candidates = []

    rules = [
        (
            ("timeout", "timed out", "time limit"),
            "Pipeline execution exceeded a time limit",
            "Inspect execution duration, resource usage, and query plans.",
        ),
        (
            (
                "schema mismatch",
                "incompatible type",
                "data type",
                "does not match expected",
                "column type",
            ),
            "Incoming data may not match the expected schema",
            "Compare source field types with the target schema.",
        ),
        (
            (
                "dependency failure",
                "upstream task failed",
                "upstream dependency",
                "dependency failed",
            ),
            "An upstream dependency may have failed",
            "Inspect the upstream task and its execution logs.",
        ),
        (
            ("source returned only",),
            "The source delivered fewer rows than expected",
            "Compare source counts, target counts, and rejected rows.",
        ),
        (
            ("ended before all expected rows were processed",),
            "Processing ended before all expected rows were processed",
            "Inspect the logs around the point of termination.",
        ),
    ]

    for keywords, cause, next_action in rules:
        if any(keyword in evidence_text for keyword in keywords):
            candidates.append({
                "cause": cause,
                "status": "supported_observation",
                "next_action": next_action,
            })

    expected_rows = incident.get("expected_rows")
    actual_rows = incident.get("actual_rows")

    # Only add the generic candidate when numeric counts are available,
    # actually differ, and a more specific row-count explanation did not match.
    if (
        expected_rows is not None
        and actual_rows is not None
        and int(expected_rows) != int(actual_rows)
    ):
        specific_row_count_causes = {
            "The source delivered fewer rows than expected",
            "Processing ended before all expected rows were processed",
        }

        if not any(
            candidate["cause"] in specific_row_count_causes
            for candidate in candidates
        ):
            candidates.append({
                "cause": "Expected and actual row counts differ",
                "status": "supported_observation",
                "next_action": (
                    "Compare source and target counts and inspect "
                    "rejected or filtered rows."
                ),
            })

    return {
        "candidates": candidates,
        "confirmed_root_cause": None,
        "note": (
            "Candidates describe evidence-supported possibilities, "
            "not confirmed explanations of the underlying failure."
        ),
    }
