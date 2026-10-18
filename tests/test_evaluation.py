
import pytest

from app.investigator import classify_evidence, assess_root_causes
from tests.run_evaluation import CASES


def test_timeout_is_classified_correctly():
    category, _, _ = classify_evidence(
        ["Pipeline timeout: execution exceeded 30 minutes"],
        0,
    )
    assert category == "timeout"


def test_schema_mismatch_is_classified_correctly():
    category, _, _ = classify_evidence(
        ["Schema mismatch: price_text does not match expected numeric type"],
        200,
    )
    assert category == "schema_mismatch"


def test_dependency_failure_is_classified_correctly():
    category, _, _ = classify_evidence(
        ["Dependency failure: upstream customer_sync task failed"],
        1000,
    )
    assert category == "dependency_failure"


def test_early_termination_is_classified_correctly():
    category, _, _ = classify_evidence(
        ["Import ended before all expected rows were processed"],
        20,
    )
    assert category == "early_termination"


def test_timeout_does_not_create_generic_row_count_candidate():
    incident = {
        "expected_rows": 500,
        "actual_rows": 500,
        "evidence": [
            {"observation": "Pipeline status is FAILED"},
            {"observation": "Expected 500 rows, but received 500"},
            {
                "observation": (
                    "[ERROR] Pipeline timeout: execution exceeded 30 minutes"
                )
            },
        ],
    }

    result = assess_root_causes(incident)
    causes = [item["cause"] for item in result["candidates"]]

    assert "Pipeline execution exceeded a time limit" in causes
    assert "Expected and actual row counts differ" not in causes
    assert result["confirmed_root_cause"] is None


def test_schema_mismatch_suppresses_generic_row_count_candidate():
    incident = {
        "expected_rows": 200,
        "actual_rows": 0,
        "evidence": [
            {"observation": "Expected 200 rows, but received 0"},
            {
                "observation": (
                    "[ERROR] Schema mismatch: price_text does not match "
                    "expected numeric type"
                )
            },
        ],
    }

    result = assess_root_causes(incident)
    causes = [item["cause"] for item in result["candidates"]]

    assert "Incoming data may not match the expected schema" in causes
    assert "Expected and actual row counts differ" not in causes
    assert result["confirmed_root_cause"] is None

def test_unknown_evidence_is_not_forced_into_a_category():
    category, hypothesis, recommendation = classify_evidence(
        ["Pipeline stopped; no additional diagnostic details available"],
        0,
    )

    assert category == "unclassified"
    assert "does not support a specific failure category" in hypothesis
    assert recommendation


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["name"])
def test_synthetic_challenge_case(case):
    category, _, _ = classify_evidence(
        case["logs"],
        case["missing_rows"],
    )

    assert category == case["expected"]

