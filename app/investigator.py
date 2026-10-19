
from app.db import get_failed_pipelines, get_connection


def _evidence_reference(item, index=0):
    if item.get("log_id") is not None:
        return f"{item.get('source', 'UNKNOWN')} · LOG-{item['log_id']}"
    if item.get("run_id") is not None:
        return f"{item.get('source', 'UNKNOWN')} · RUN-{item['run_id']}"
    return f"EVIDENCE-{index + 1}"


def _completeness(expected_rows, actual_rows):
    if expected_rows is None or actual_rows is None:
        return None
    expected_rows = int(expected_rows)
    actual_rows = int(actual_rows)
    if expected_rows == 0:
        return 100.0 if actual_rows == 0 else None
    return round(actual_rows * 100.0 / expected_rows, 2)


def _optional_int(value):
    return int(value) if value is not None else None


def _build_run_comparison(run_id, expected_rows, actual_rows, log_rows,
                          last_success, baseline, baseline_logs):
    """Compare the failed run with its latest successful baseline."""
    if last_success is None:
        return {
            "status": "unavailable",
            "message": "No earlier successful run is available for comparison.",
            "differences": [],
            "new_or_changed_logs": [],
        }

    baseline_run_id = int(last_success[0])
    current_expected = _optional_int(expected_rows)
    current_actual = _optional_int(actual_rows)
    baseline_expected = _optional_int(last_success[1])
    baseline_actual = _optional_int(last_success[2])
    current_reference = f"OPSINTEL.PIPELINE_RUNS · RUN-{int(run_id)}"
    baseline_reference = f"OPSINTEL.PIPELINE_RUNS · RUN-{baseline_run_id}"
    baseline_messages = {str(row[2]).strip().lower() for row in baseline_logs}
    new_logs = [
        {
            "log_id": int(row[0]),
            "level": str(row[1]),
            "message": str(row[2]),
            "timestamp": str(row[3]),
            "reference": f"OPSINTEL.PIPELINE_LOGS · LOG-{int(row[0])}",
        }
        for row in log_rows
        if str(row[2]).strip().lower() not in baseline_messages
    ]
    current_completeness = _completeness(expected_rows, actual_rows)
    baseline_completeness = _completeness(baseline_expected, baseline_actual)

    def difference(current, previous):
        return None if current is None or previous is None else current - previous

    differences = [
        {
            "metric": "Expected rows",
            "current": current_expected,
            "baseline": baseline_expected,
            "delta": difference(current_expected, baseline_expected),
            "unit": "rows",
            "evidence_refs": [current_reference, baseline_reference],
        },
        {
            "metric": "Actual rows",
            "current": current_actual,
            "baseline": baseline_actual,
            "delta": difference(current_actual, baseline_actual),
            "unit": "rows",
            "evidence_refs": [current_reference, baseline_reference],
        },
        {
            "metric": "Completeness",
            "current": current_completeness,
            "baseline": baseline_completeness,
            "delta": (
                round(current_completeness - baseline_completeness, 2)
                if current_completeness is not None
                and baseline_completeness is not None
                else None
            ),
            "unit": "percentage points",
            "evidence_refs": [current_reference, baseline_reference],
        },
    ]
    if new_logs:
        differences.append({
            "metric": "New or changed log messages",
            "current": len(new_logs),
            "baseline": len(baseline_logs),
            "delta": len(new_logs),
            "unit": "messages",
            "evidence_refs": [item["reference"] for item in new_logs],
        })

    return {
        "status": "available",
        "current_run": {
            "run_id": int(run_id),
            "expected_rows": current_expected,
            "actual_rows": current_actual,
            "completeness_pct": current_completeness,
        },
        "last_successful_run": {
            "run_id": baseline_run_id,
            "expected_rows": baseline_expected,
            "actual_rows": baseline_actual,
            "completeness_pct": baseline_completeness,
            "run_time": str(last_success[3]),
        },
        "historical_baseline": {
            "average_actual_rows": (
                float(baseline[0]) if baseline and baseline[0] is not None else None
            ),
            "average_completeness_pct": (
                float(baseline[1]) if baseline and baseline[1] is not None else None
            ),
            "successful_runs": int(baseline[2]) if baseline else 0,
        },
        "differences": differences,
        "new_or_changed_logs": new_logs,
    }


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
    )) or (missing_rows is not None and missing_rows > 0):
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
              AND (
                    RUN_TIME < (
                        SELECT RUN_TIME
                        FROM OPSINTEL.PIPELINE_RUNS
                        WHERE RUN_ID = {run_id!d}
                    )
                    OR (
                        RUN_TIME = (
                            SELECT RUN_TIME
                            FROM OPSINTEL.PIPELINE_RUNS
                            WHERE RUN_ID = {run_id!d}
                        )
                        AND RUN_ID <= {run_id!d}
                    )
                  )
            ORDER BY RUN_TIME DESC, RUN_ID DESC
            LIMIT 5
            """,
            {"pipeline_name": incident[1], "run_id": int(run_id)},
        ).fetchall()

        last_success = connection.execute(
            """
            SELECT
                RUN_ID,
                EXPECTED_ROWS,
                ACTUAL_ROWS,
                TO_CHAR(RUN_TIME, 'YYYY-MM-DD HH24:MI:SS')
            FROM OPSINTEL.PIPELINE_RUNS
            WHERE PIPELINE_NAME = {pipeline_name}
              AND RUN_STATUS = 'SUCCESS'
              AND (
                    RUN_TIME < (
                        SELECT RUN_TIME
                        FROM OPSINTEL.PIPELINE_RUNS
                        WHERE RUN_ID = {run_id!d}
                    )
                    OR (
                        RUN_TIME = (
                            SELECT RUN_TIME
                            FROM OPSINTEL.PIPELINE_RUNS
                            WHERE RUN_ID = {run_id!d}
                        )
                        AND RUN_ID < {run_id!d}
                    )
                  )
            ORDER BY RUN_TIME DESC, RUN_ID DESC
            LIMIT 1
            """,
            {"pipeline_name": incident[1], "run_id": int(run_id)},
        ).fetchone()

        baseline = connection.execute(
            """
            SELECT
                ROUND(AVG(ACTUAL_ROWS), 2),
                ROUND(AVG(
                    CASE
                        WHEN EXPECTED_ROWS IS NULL OR ACTUAL_ROWS IS NULL
                            THEN NULL
                        WHEN EXPECTED_ROWS = 0 AND ACTUAL_ROWS = 0 THEN 100
                        WHEN EXPECTED_ROWS = 0 THEN NULL
                        ELSE ACTUAL_ROWS * 100.0 / EXPECTED_ROWS
                    END
                ), 2),
                COUNT(*)
            FROM OPSINTEL.PIPELINE_RUNS
            WHERE PIPELINE_NAME = {pipeline_name}
              AND RUN_STATUS = 'SUCCESS'
              AND (
                    RUN_TIME < (
                        SELECT RUN_TIME
                        FROM OPSINTEL.PIPELINE_RUNS
                        WHERE RUN_ID = {run_id!d}
                    )
                    OR (
                        RUN_TIME = (
                            SELECT RUN_TIME
                            FROM OPSINTEL.PIPELINE_RUNS
                            WHERE RUN_ID = {run_id!d}
                        )
                        AND RUN_ID < {run_id!d}
                    )
                  )
            """,
            {"pipeline_name": incident[1], "run_id": int(run_id)},
        ).fetchone()

        baseline_logs = []
        if last_success is not None:
            baseline_logs = connection.execute(
                """
                SELECT DISTINCT LOG_ID, LOG_LEVEL, LOG_MESSAGE, LOG_TIME
                FROM OPSINTEL.PIPELINE_LOGS
                WHERE RUN_ID = {run_id!d}
                ORDER BY LOG_ID
                """,
                {"run_id": int(last_success[0])},
            ).fetchall()
    finally:
        connection.close()

    expected_rows = _optional_int(incident[2])
    actual_rows = _optional_int(incident[3])
    missing_rows = _optional_int(incident[4])
    excess_rows = (
        _optional_int(incident[6])
        if len(incident) > 6
        else (
            max(actual_rows - expected_rows, 0)
            if expected_rows is not None and actual_rows is not None
            else None
        )
    )
    log_messages = [str(log[2]) for log in log_rows]

    if expected_rows is None and actual_rows is None:
        row_count_observation = "Expected and actual row-count metadata is unavailable"
    elif expected_rows is None:
        row_count_observation = (
            f"Expected row-count metadata is unavailable; received {actual_rows} rows"
        )
    elif actual_rows is None:
        row_count_observation = (
            f"Expected {expected_rows} rows; actual row-count metadata is unavailable"
        )
    else:
        row_count_observation = (
            f"Expected {expected_rows} rows, but received {actual_rows}"
        )

    evidence = [
        {
            "type": "pipeline_status",
            "observation": f"Pipeline status is {incident[5]}",
            "source": "OPSINTEL.PIPELINE_RUNS",
            "run_id": int(run_id),
        },
        {
            "type": "row_count",
            "observation": row_count_observation,
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
    comparison = _build_run_comparison(
        run_id,
        expected_rows,
        actual_rows,
        log_rows,
        last_success,
        baseline,
        baseline_logs,
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
                "expected_rows": _optional_int(row[2]),
                "actual_rows": _optional_int(row[3]),
                "run_time": str(row[4]),
            }
            for row in history_rows
        ],
        "comparison": comparison,
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

    def matching_evidence(keywords):
        return [
            {
                "reference": _evidence_reference(item, index),
                "observation": item.get("observation", ""),
            }
            for index, item in enumerate(evidence)
            if any(
                keyword in item.get("observation", "").lower()
                for keyword in keywords
            )
        ]

    def add_candidate(cause, next_action, support):
        if support:
            candidates.append({
                "cause": cause,
                "status": "supported_observation",
                "next_action": next_action,
                "supporting_evidence": support,
            })

    candidates = []
    row_count_support = [
        {
            "reference": _evidence_reference(item, index),
            "observation": item.get("observation", ""),
        }
        for index, item in enumerate(evidence)
        if item.get("type") == "row_count"
    ]

    category_candidate = {
        "conflicting_evidence": (
            "The log trail contains conflicting completion signals",
            "Verify the final orchestrator state and inspect the latest log.",
            (
                "completed successfully", "finished successfully",
                "all expected rows processed", "error", "failed", "aborted",
            ),
        ),
        "delayed_run": (
            "The pipeline may have started later than scheduled",
            "Compare scheduled and actual start times and upstream timing.",
            ("started late", "schedule delay", "delayed by", "missed sla"),
        ),
        "duplicate_data": (
            "The run may contain duplicate or excess rows",
            "Compare source and target keys and inspect retry behavior.",
            ("duplicate rows", "duplicate records", "more rows than expected"),
        ),
    }.get(incident.get("category"))

    if category_candidate:
        support = matching_evidence(category_candidate[2])
        if incident.get("category") == "duplicate_data" and not support:
            support = row_count_support
        add_candidate(category_candidate[0], category_candidate[1], support)

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
            add_candidate(cause, next_action, matching_evidence(keywords))

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

    if (
        expected_rows is not None
        and actual_rows is not None
        and int(expected_rows) != int(actual_rows)
    ):
        for candidate in candidates:
            if candidate["cause"] in specific_row_count_causes:
                existing = {
                    item["reference"]
                    for item in candidate["supporting_evidence"]
                }
                candidate["supporting_evidence"].extend(
                    item for item in row_count_support
                    if item["reference"] not in existing
                )

    # Add a generic row-count candidate only when no specific explanation
    # is already supported by the available evidence.
    if (
        expected_rows is not None
        and actual_rows is not None
        and int(expected_rows) != int(actual_rows)
        and not has_specific_candidate
    ):
        add_candidate(
            "Expected and actual row counts differ",
            "Compare source and target counts and inspect rejected or filtered rows.",
            row_count_support,
        )

    return {
        "candidates": candidates,
        "confirmed_root_cause": None,
        "resolution_status": "candidates_only" if candidates else "unresolved",
        "unresolved_reason": (
            None if candidates else
            "The available evidence does not support a candidate explanation."
        ),
        "note": (
            "Candidates describe evidence-supported possibilities, "
            "not confirmed explanations of the underlying failure."
        ),
    }


def attach_comparison_support(incident, assessment):
    """Link run differences to candidates through shared evidence references."""
    comparison = incident.get("comparison")
    if not comparison or comparison.get("status") != "available":
        return

    for difference in comparison.get("differences", []):
        difference_refs = set(difference.get("evidence_refs", []))
        difference["supports"] = [] if not difference.get("delta") else [
            candidate["cause"]
            for candidate in assessment.get("candidates", [])
            if difference_refs & {
                item["reference"]
                for item in candidate.get("supporting_evidence", [])
            }
        ]
