
from app.investigator import assess_root_causes


def test_root_cause_is_not_claimed_as_confirmed():
    incident = {
        "evidence": [
            {"observation": "Source returned only 80 rows"}
        ]
    }

    result = assess_root_causes(incident)

    assert result["confirmed_root_cause"] is None
    assert len(result["candidates"]) > 0


def test_root_cause_candidates_are_supported_observations():
    incident = {
        "evidence": [
            {"observation": "Source returned only 80 rows"},
            {
                "observation": (
                    "Import ended before all expected rows were processed"
                )
            },
        ]
    }

    result = assess_root_causes(incident)

    for candidate in result["candidates"]:
        assert candidate["status"] == "supported_observation"

def test_timeout_evidence_produces_timeout_candidate():
    incident = {
        "evidence": [
            {"observation": "Pipeline timeout: execution exceeded 30 minutes"}
        ]
    }

    result = assess_root_causes(incident)

    assert any(
        "time limit" in candidate["cause"].lower()
        for candidate in result["candidates"]
    )


def test_schema_mismatch_evidence_produces_schema_candidate():
    incident = {
        "evidence": [
            {
                "observation": (
                    "Schema mismatch: incoming field price_text "
                    "does not match expected numeric type"
                )
            }
        ]
    }

    result = assess_root_causes(incident)

    assert any(
        "schema" in candidate["cause"].lower()
        for candidate in result["candidates"]
    )


def test_empty_evidence_does_not_invent_root_causes():
    incident = {"evidence": []}

    result = assess_root_causes(incident)

    assert result["candidates"] == []
    assert result["confirmed_root_cause"] is None

