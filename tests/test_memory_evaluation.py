import pytest

from scripts.evaluate_memory import evaluate


def _incident(run_id, message):
    return {"run_id": run_id, "category": "timeout", "evidence": [
        {"type": "pipeline_log", "reference": f"LOG-{run_id}", "observation": message},
    ]}


def test_prequential_evaluation_uses_only_prior_confirmations():
    events = [
        {"event_id": "q1", "event_type": "query", "timestamp": "2026-10-30T09:00:00+00:00", "run_id": 2,
         "incident": _incident(2, "query timed out waiting on lock"), "expected_category": "timeout", "expected_cause_id": "lock-wait"},
        {"event_id": "c1", "event_type": "confirmation", "timestamp": "2026-10-30T10:00:00+00:00", "run_id": 1,
         "incident": _incident(1, "query timed out waiting on lock"), "cause_id": "lock-wait"},
        {"event_id": "q2", "event_type": "query", "timestamp": "2026-10-30T11:00:00+00:00", "run_id": 3,
         "incident": _incident(3, "query timed out waiting on lock"), "expected_category": "timeout", "expected_cause_id": "lock-wait"},
    ]
    report = evaluate(events)
    assert report["results"][0]["memory_size"] == 0
    assert report["results"][0]["abstained"]
    assert report["results"][1]["memory_size"] == 1
    assert report["results"][1]["selective_match_cause_id"] == "lock-wait"
    assert report["learning_curve"][0]["confirmed_records_available"] == 0
    assert report["learning_curve"][1]["confirmed_records_available"] == 1


def test_prequential_evaluation_does_not_match_case_to_itself():
    events = [
        {"event_id": "c1", "event_type": "confirmation", "timestamp": "2026-10-30T10:00:00+00:00", "run_id": 1,
         "incident": _incident(1, "timeout waiting for lock"), "cause_id": "lock-wait"},
        {"event_id": "q1", "event_type": "query", "timestamp": "2026-10-30T11:00:00+00:00", "run_id": 1,
         "incident": _incident(1, "timeout waiting for lock"), "expected_category": "timeout", "expected_cause_id": "lock-wait"},
    ]
    assert evaluate(events)["results"][0]["abstained"]


def test_confirmation_requires_unique_run_and_cause_id():
    event = {"event_id": "c1", "event_type": "confirmation", "timestamp": "2026-10-30T10:00:00+00:00", "run_id": 1,
             "incident": _incident(1, "timeout waiting for lock")}
    with pytest.raises(ValueError, match="cause ID"):
        evaluate([event])


def test_same_timestamp_confirmation_is_not_available_to_query():
    events = [
        {"event_id": "a-confirm", "event_type": "confirmation", "timestamp": "2026-10-30T10:00:00+00:00", "run_id": 1,
         "incident": _incident(1, "timeout waiting for lock"), "cause_id": "lock-wait"},
        {"event_id": "b-query", "event_type": "query", "timestamp": "2026-10-30T10:00:00+00:00", "run_id": 2,
         "incident": _incident(2, "timeout waiting for lock"), "expected_cause_id": "lock-wait"},
    ]
    assert evaluate(events)["results"][0]["abstained"]
