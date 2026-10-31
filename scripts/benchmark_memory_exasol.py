"""Read-only repeated benchmark of Verified Incident Memory on live Exasol."""

import argparse
import json
import math
import platform
import resource
import statistics
import sys
import time
import tracemalloc
from datetime import datetime, timezone

from app import memory
from app.db import get_connection
from app.investigator import investigate_pipeline


def percentile(values, fraction):
    """Return the nearest-rank percentile."""
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * fraction) - 1)]


def result_signature(result):
    """Fields expected to remain stable between read-only retrievals."""
    return [
        (item["matched_incident_id"], item["similarity_score"])
        for item in result["matches"]
    ]


def benchmark(run_id, *, warmups=3, repetitions=30, expected_history=None,
              expected_match=None):
    if warmups < 0 or repetitions < 1:
        raise ValueError("warmups must be >= 0 and repetitions must be positive")

    connection = get_connection()
    try:
        history_count = int(connection.execute("""
            SELECT COUNT(*) FROM OPSINTEL.CONFIRMED_INCIDENTS
            WHERE STATUS = 'active'
        """).fetchone()[0])
        match_rows_before = int(connection.execute("""
            SELECT COUNT(*) FROM OPSINTEL.INCIDENT_MATCHES
            WHERE SOURCE_RUN_ID = {run_id!d}
        """, {"run_id": int(run_id)}).fetchone()[0])
    finally:
        connection.close()

    if expected_history is not None and history_count != expected_history:
        raise ValueError(
            f"expected {expected_history} active memories, found {history_count}"
        )

    incident = investigate_pipeline(int(run_id))
    if incident is None:
        raise ValueError(f"incident run {run_id} was not found")

    previous_signature = None
    final_result = None
    for _ in range(warmups):
        final_result = memory.similar_incidents(incident, record=False)
        signature = result_signature(final_result)
        if previous_signature is not None and signature != previous_signature:
            raise AssertionError("read-only retrieval changed during warm-up")
        previous_signature = signature

    tracemalloc.start()
    timings = []
    for _ in range(repetitions):
        started = time.perf_counter()
        final_result = memory.similar_incidents(incident, record=False)
        timings.append((time.perf_counter() - started) * 1000)
        signature = result_signature(final_result)
        if previous_signature is not None and signature != previous_signature:
            tracemalloc.stop()
            raise AssertionError("retrieval result changed between repetitions")
        previous_signature = signature
    _, peak_python_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    if expected_match is not None:
        top_match = final_result["matches"][0]["matched_incident_id"] if final_result["matches"] else None
        if top_match != expected_match:
            raise AssertionError(f"expected top match {expected_match}, found {top_match}")

    if any(item["historical_run_id"] == int(run_id) for item in final_result["matches"]):
        raise AssertionError("retrieval included the query run itself")
    if any(not item["historical_evidence"] for item in final_result["matches"]):
        raise AssertionError("retrieved memory has no cited historical evidence")

    connection = get_connection()
    try:
        match_rows_after = int(connection.execute("""
            SELECT COUNT(*) FROM OPSINTEL.INCIDENT_MATCHES
            WHERE SOURCE_RUN_ID = {run_id!d}
        """, {"run_id": int(run_id)}).fetchone()[0])
    finally:
        connection.close()
    if match_rows_after != match_rows_before:
        raise AssertionError("read-only benchmark changed incident match rows")

    rss_units = "bytes" if platform.system() == "Darwin" else "KiB"
    rss_peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {
        "measured_at_utc": datetime.now(timezone.utc).isoformat(),
        "query_run_id": int(run_id),
        "active_history_count": history_count,
        "warmups": warmups,
        "repetitions": repetitions,
        "latency_ms": {
            "min": round(min(timings), 3),
            "median": round(statistics.median(timings), 3),
            "p95_nearest_rank": round(percentile(timings, 0.95), 3),
            "max": round(max(timings), 3),
            "samples": [round(value, 3) for value in timings],
        },
        "retrieval": {
            "status": final_result["status"],
            "candidate_count": len(final_result["matches"]),
            "top_match_ids_and_scores": result_signature(final_result),
            "correctness_check": (
                "expected top match verified" if expected_match is not None
                else "stable results, query-run exclusion, and evidence references verified; semantic ground truth not supplied"
            ),
        },
        "memory": {
            "python_tracemalloc_peak_bytes_during_measurement": peak_python_bytes,
            "process_peak_rss": rss_peak,
            "process_peak_rss_units": rss_units,
            "exasol_server_memory": "not measured",
        },
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "fingerprint_version": memory.FINGERPRINT_VERSION,
            "similarity_threshold": memory.min_similarity_threshold(),
            "query_cache": "Exasol/application default; not explicitly changed",
        },
        "database_mutations": "none; retrieval called with record=False",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", type=int, required=True, help="source incident run to query")
    parser.add_argument("--warmups", type=int, default=3)
    parser.add_argument("--repetitions", type=int, default=30)
    parser.add_argument("--expected-history", type=int,
                        help="fail unless this exact number of active memories exists")
    parser.add_argument("--expected-match",
                        help="pre-registered top-match incident ID; omit for structural checks only")
    args = parser.parse_args()
    print(json.dumps(benchmark(
        args.run_id, warmups=args.warmups, repetitions=args.repetitions,
        expected_history=args.expected_history, expected_match=args.expected_match,
    ), indent=2))


if __name__ == "__main__":
    main()
