
from app.db import get_failed_pipelines, get_connection


def classify_evidence(
    log_messages,
    missing_rows,
    expected_rows=None,
    actual_rows=None,
):
    """Classify evidence without claiming an unverified root cause."""
    benign_phrases = (
        "no timeout",
        "without timeout",
        "timeout setting",
        "timeout threshold configured",
    )
    text = " ".join(
        message.lower()
        for message in log_messages
        if not any(phrase in message.lower() for phrase in benign_phrases)
    )

    has_success_signal = any(phrase in text for phrase in (
        "completed successfully",
        "finished successfully",
        "all expected rows processed",
    ))
    has_failure_signal = any(phrase in text for phrase in (
        "error",
        "failed",
        "timeout",
        "aborted",
        "terminated",
    ))

    if has_success_signal and has_failure_signal:
        return (
            "conflicting_evidence",
            "The retrieved logs contain both success and failure signals. "
            "The run state cannot be resolved from this evidence alone.",
            "Verify the final orchestrator state and inspect the latest log "
            "record before assigning a cause.",
        )

    if any(phrase in text for phrase in (
        "started late",
        "schedule delay",
        "delayed by",
        "missed sla",
        "missed its sla",
    )):
        return (
            "delayed_run",
            "Logs report a delayed start or missed schedule. The source of "
            "the delay is not confirmed.",
            "Compare scheduled and actual start times, then inspect upstream "
            "queue and dependency timing.",
        )

    if any(phrase in text for phrase in (
        "duplicate rows",
        "duplicate records",
        "more rows than expected",
    )) or (
        expected_rows is not None
        and actual_rows is not None
        and int(actual_rows) > int(expected_rows)
    ):
        return (
            "duplicate_data",
            "The available evidence indicates more rows than expected or "
            "possible duplicate records. The duplication point is unknown.",
            "Compare source keys with target keys and inspect retry or "
            "deduplication logs.",
        )

    if any(word in text for word in (
        "timeout",
        "timed out",
        "time limit",
        "deadline exceeded",
        "execution exceeded",
    )):
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
        "invalid cast",
        "type conversion",
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
        "prerequisite task failed",
    )):
        return (
            "dependency_failure",
            "Logs indicate an upstream dependency failure. "
            "The upstream task's failure should be investigated.",
            "Inspect the upstream task status, its logs, and dependency "
            "execution order.",
        )

    # Prefer a specific early-termination signal over a generic row-count issue.
    if any(phrase in text for phrase in (
        "ended before all expected rows were processed",
        "aborted before completion",
        "processing stopped early",
        "terminated before completion",
    )):
        return (
            "early_termination",
            "Logs report that processing ended before all expected rows "
            "were processed. The underlying reason is not confirmed.",
            "Inspect the execution logs around termination and identify "
            "the first reported error.",
        )

    if any(phrase in text for phrase in (
        "source returned only",
        "fewer rows than expected",
        "row shortfall",
        "missing rows",
    )) or missing_rows > 0:
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
            SELECT DISTINCT LOG_ID, LOG_LEVEL, LOG_MESSAGE, LOG_TIME
            FROM OPSINTEL.PIPELINE_LOGS
            WHERE RUN_ID = {run_id!d}
            ORDER BY LOG_ID
            """,
            {"run_id": int(run_id)},
        )
        log_rows = result.fetchall()

        history_rows = connection.execute(
            """
            SELECT
                RUN_ID,
                RUN_STATUS,
                EXPECTED_ROWS,
                ACTUAL_ROWS,
                TO_CHAR(RUN_TIME, 'YYYY-MM-DD HH24:MI:SS')
            FROM OPSINTEL.PIPELINE_RUNS
            WHERE PIPELINE_NAME = {pipeline_name}
            ORDER BY RUN_TIME DESC, RUN_ID DESC
            LIMIT 5
            """,
            {"pipeline_name": incident[1]},
        ).fetchall()
    finally:
        connection.close()

    expected_rows = int(incident[2])
    actual_rows = int(incident[3])
    missing_rows = int(incident[4])
    excess_rows = (
        int(incident[6])
        if len(incident) > 6
        else max(actual_rows - expected_rows, 0)
    )
    log_messages = [str(log[2]) for log in log_rows]

    evidence = [
        {
            "type": "pipeline_status",
            "observation": f"Pipeline status is {incident[5]}",
            "source": "OPSINTEL.PIPELINE_RUNS",
            "run_id": int(run_id),
        },
        {
            "type": "row_count",
            "observation": (
                f"Expected {expected_rows} rows, "
                f"but received {actual_rows}"
            ),
            "source": "OPSINTEL.PIPELINE_RUNS",
            "run_id": int(run_id),
        },
    ]

    for log in log_rows:
        evidence.append({
            "type": "pipeline_log",
            "observation": f"[{log[1]}] {log[2]}",
            "source": "OPSINTEL.PIPELINE_LOGS",
            "log_id": int(log[0]),
            "timestamp": str(log[3]),
        })

    category, hypothesis, recommended_action = classify_evidence(
        log_messages,
        missing_rows,
        expected_rows,
        actual_rows,
    )

    return {
        "run_id": int(run_id),
        "pipeline_name": incident[1],
        "status": incident[5],
        "expected_rows": expected_rows,
        "actual_rows": actual_rows,
        "missing_rows": missing_rows,
        "excess_rows": excess_rows,
        "category": category,
        "hypothesis": hypothesis,
        "confidence": "low",
        "recommended_action": recommended_action,
        "evidence": evidence,
        "history": [
            {
                "run_id": int(row[0]),
                "status": row[1],
                "expected_rows": int(row[2]),
                "actual_rows": int(row[3]),
                "run_time": str(row[4]),
            }
            for row in history_rows
        ],
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

    category_candidate = {
        "conflicting_evidence": (
            "The log trail contains conflicting completion signals",
            "Verify the final orchestrator state and inspect the latest log.",
        ),
        "delayed_run": (
            "The pipeline may have started later than scheduled",
            "Compare scheduled and actual start times and upstream timing.",
        ),
        "duplicate_data": (
            "The run may contain duplicate or excess rows",
            "Compare source and target keys and inspect retry behavior.",
        ),
    }.get(incident.get("category"))

    if category_candidate:
        candidates.append({
            "cause": category_candidate[0],
            "status": "supported_observation",
            "next_action": category_candidate[1],
        })

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

    specific_row_count_causes = {
        "The source delivered fewer rows than expected",
        "Processing ended before all expected rows were processed",
    }

    specific_failure_causes = {
        "The log trail contains conflicting completion signals",
        "The pipeline may have started later than scheduled",
        "The run may contain duplicate or excess rows",
        "Pipeline execution exceeded a time limit",
        "Incoming data may not match the expected schema",
        "An upstream dependency may have failed",
    }

    has_specific_candidate = any(
        candidate["cause"] in (
            specific_row_count_causes | specific_failure_causes
        )
        for candidate in candidates
    )

    # Add a generic row-count candidate only when no specific explanation
    # is already supported by the available evidence.
    if (
        expected_rows is not None
        and actual_rows is not None
        and int(expected_rows) != int(actual_rows)
        and not has_specific_candidate
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
