from scripts.benchmark_memory_exasol import percentile, result_signature


def test_percentile_uses_nearest_rank():
    assert percentile([5, 1, 3, 2, 4], 0.95) == 5
    assert percentile([5, 1, 3, 2, 4], 0.50) == 3


def test_result_signature_contains_only_stable_candidate_identity_and_score():
    result = {
        "matches": [
            {"matched_incident_id": "incident-1", "similarity_score": 0.75,
             "match_id": "generated-a", "historical_evidence": [{"reference": "log"}]},
        ]
    }
    assert result_signature(result) == [("incident-1", 0.75)]
