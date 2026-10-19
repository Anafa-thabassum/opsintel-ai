import json
from unittest.mock import Mock

import httpx

from app.llm import summarize_investigation


INCIDENT = {
    "run_id": 1,
    "pipeline_name": "daily_sales_import",
    "status": "FAILED",
    "expected_rows": 100,
    "actual_rows": 80,
    "missing_rows": 20,
    "category": "early_termination",
    "confidence": "low",
    "recommended_action": "Inspect the logs around termination.",
    "evidence": [
        {
            "type": "pipeline_log",
            "observation": "Processing ended before all expected rows were processed",
            "source": "OPSINTEL.PIPELINE_LOGS",
            "log_id": 3,
        }
    ],
}

ROOT_CAUSES = {
    "candidates": [
        {
            "cause": "Processing ended before all expected rows were processed",
            "status": "supported_observation",
            "next_action": "Inspect the logs around the point of termination.",
        }
    ],
    "confirmed_root_cause": None,
}


def test_llm_summary_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("OPSINTEL_LLM_ENABLED", raising=False)
    client = Mock()

    result = summarize_investigation(INCIDENT, ROOT_CAUSES, client)

    assert result["status"] == "disabled"
    assert result["summary"] is None
    client.post.assert_not_called()


def test_llm_summary_requires_api_key(monkeypatch):
    monkeypatch.setenv("OPSINTEL_LLM_ENABLED", "true")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    result = summarize_investigation(INCIDENT, ROOT_CAUSES)

    assert result["status"] == "unavailable"
    assert result["summary"] is None


def test_llm_summary_uses_structured_evidence_only(monkeypatch):
    monkeypatch.setenv("OPSINTEL_LLM_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPSINTEL_LLM_MODEL", "test-model")
    response = Mock()
    response.json.return_value = {
        "output": [
            {
                "content": [
                    {
                        "type": "output_text",
                        "text": json.dumps({
                            "claims": [{
                                "statement": (
                                    "Processing ended before all expected rows "
                                    "were processed."
                                ),
                                "evidence_refs": [
                                    "OPSINTEL.PIPELINE_LOGS · LOG-3"
                                ],
                                "evidence_quotes": [{
                                    "reference": "OPSINTEL.PIPELINE_LOGS · LOG-3",
                                    "quote": (
                                        "Processing ended before all expected "
                                        "rows were processed"
                                    ),
                                }],
                            }],
                            "evidence_gaps": ["The first termination error"],
                        }),
                    }
                ]
            }
        ]
    }
    client = Mock()
    client.post.return_value = response

    result = summarize_investigation(INCIDENT, ROOT_CAUSES, client)

    assert result["status"] == "generated"
    assert result["model"] == "test-model"
    assert result["summary"] == (
        "Processing ended before all expected rows were processed."
    )
    assert result["claims"] == [{
        "statement": "Processing ended before all expected rows were processed.",
        "evidence_refs": ["OPSINTEL.PIPELINE_LOGS · LOG-3"],
    }]
    assert result["evidence_gaps"] == ["The first termination error"]
    assert result["evidence_refs"] == [
        "OPSINTEL.PIPELINE_LOGS · LOG-3"
    ]
    request = client.post.call_args.kwargs
    assert request["json"]["store"] is False
    assert request["json"]["text"]["format"]["strict"] is True
    schema = request["json"]["text"]["format"]["schema"]
    assert "claims" in schema["properties"]
    claim_schema = schema["properties"]["claims"]["items"]
    assert "evidence_quotes" in claim_schema["required"]
    assert "untrusted data" in request["json"]["instructions"]
    assert json.loads(request["json"]["input"])["confirmed_root_cause"] is None
    assert request["headers"]["Authorization"] == "Bearer test-key"


def test_llm_failure_falls_back_without_breaking_investigation(monkeypatch):
    monkeypatch.setenv("OPSINTEL_LLM_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    client = Mock()
    client.post.side_effect = httpx.ConnectError("offline")

    result = summarize_investigation(INCIDENT, ROOT_CAUSES, client)

    assert result["status"] == "unavailable"
    assert result["summary"] is None
    assert "cannot confirm" in result["safety_note"]


def test_llm_timeout_falls_back_without_breaking_investigation(monkeypatch):
    monkeypatch.setenv("OPSINTEL_LLM_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    client = Mock()
    client.post.side_effect = httpx.TimeoutException("timed out")

    result = summarize_investigation(INCIDENT, ROOT_CAUSES, client)

    assert result["status"] == "unavailable"
    assert result["summary"] is None
    assert result["claims"] == []


def test_llm_rejects_unknown_evidence_references(monkeypatch):
    monkeypatch.setenv("OPSINTEL_LLM_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    response = Mock()
    response.json.return_value = {
        "output_text": json.dumps({
            "claims": [{
                "statement": "A database observation was invented.",
                "evidence_refs": ["OPSINTEL.PIPELINE_LOGS · LOG-999"],
            }],
            "evidence_gaps": [],
        })
    }
    client = Mock()
    client.post.return_value = response

    result = summarize_investigation(INCIDENT, ROOT_CAUSES, client)

    assert result["status"] == "unavailable"
    assert result["summary"] is None


def test_llm_rejects_a_single_ungrounded_claim(monkeypatch):
    monkeypatch.setenv("OPSINTEL_LLM_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    response = Mock()
    response.json.return_value = {
        "output_text": json.dumps({
            "claims": [
                {
                    "statement": "Processing ended before completion.",
                    "evidence_refs": ["OPSINTEL.PIPELINE_LOGS · LOG-3"],
                },
                {
                    "statement": "The worker ran out of memory.",
                    "evidence_refs": ["OPSINTEL.PIPELINE_LOGS · LOG-404"],
                },
            ],
            "evidence_gaps": [],
        })
    }
    client = Mock()
    client.post.return_value = response

    result = summarize_investigation(INCIDENT, ROOT_CAUSES, client)

    assert result["status"] == "unavailable"
    assert result["claims"] == []


def test_llm_rejects_malformed_structured_output(monkeypatch):
    monkeypatch.setenv("OPSINTEL_LLM_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    response = Mock()
    response.json.return_value = {"output_text": "not-json"}
    client = Mock()
    client.post.return_value = response

    result = summarize_investigation(INCIDENT, ROOT_CAUSES, client)

    assert result["status"] == "unavailable"
    assert result["evidence_refs"] == []


def test_llm_rejects_incomplete_structured_output(monkeypatch):
    monkeypatch.setenv("OPSINTEL_LLM_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    response = Mock()
    response.json.return_value = {
        "output_text": json.dumps({
            "claims": [{
                "statement": "Processing ended before completion.",
                "evidence_refs": ["OPSINTEL.PIPELINE_LOGS · LOG-3"],
            }],
            "evidence_gaps": [],
        })
    }
    client = Mock()
    client.post.return_value = response

    result = summarize_investigation(INCIDENT, ROOT_CAUSES, client)

    assert result["status"] == "unavailable"
    assert result["claims"] == []


def test_llm_rate_limit_falls_back_without_leaking_credentials(monkeypatch):
    api_key = "private-test-key-that-must-not-leak"
    monkeypatch.setenv("OPSINTEL_LLM_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", api_key)
    request = httpx.Request("POST", "https://api.openai.com/v1/responses")
    rate_limited = httpx.Response(429, request=request)
    response = Mock()
    response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "rate limited",
        request=request,
        response=rate_limited,
    )
    client = Mock()
    client.post.return_value = response

    result = summarize_investigation(INCIDENT, ROOT_CAUSES, client)

    assert result["status"] == "unavailable"
    assert api_key not in json.dumps(result)


def test_llm_rejects_fabricated_metric_with_valid_reference(monkeypatch):
    monkeypatch.setenv("OPSINTEL_LLM_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    response = Mock()
    response.json.return_value = {
        "output_text": json.dumps({
            "claims": [{
                "statement": "The run was delayed by 47 minutes.",
                "evidence_refs": ["OPSINTEL.PIPELINE_LOGS · LOG-3"],
                "evidence_quotes": [{
                    "reference": "OPSINTEL.PIPELINE_LOGS · LOG-3",
                    "quote": "Processing ended before all expected rows were processed",
                }],
            }],
            "evidence_gaps": [],
        })
    }
    client = Mock()
    client.post.return_value = response

    result = summarize_investigation(INCIDENT, ROOT_CAUSES, client)

    assert result["status"] == "unavailable"
    assert result["claims"] == []


def test_llm_rejects_fabricated_log_claim_with_valid_reference(monkeypatch):
    monkeypatch.setenv("OPSINTEL_LLM_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    response = Mock()
    response.json.return_value = {
        "output_text": json.dumps({
            "claims": [{
                "statement": "The worker ran out of memory.",
                "evidence_refs": ["OPSINTEL.PIPELINE_LOGS · LOG-3"],
                "evidence_quotes": [{
                    "reference": "OPSINTEL.PIPELINE_LOGS · LOG-3",
                    "quote": "Processing ended before all expected rows were processed",
                }],
            }],
            "evidence_gaps": [],
        })
    }
    client = Mock()
    client.post.return_value = response

    result = summarize_investigation(INCIDENT, ROOT_CAUSES, client)

    assert result["status"] == "unavailable"
    assert result["claims"] == []


def test_llm_rejects_confirmed_cause_language(monkeypatch):
    monkeypatch.setenv("OPSINTEL_LLM_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    response = Mock()
    response.json.return_value = {
        "output_text": json.dumps({
            "claims": [{
                "statement": "The root cause was early termination.",
                "evidence_refs": ["OPSINTEL.PIPELINE_LOGS · LOG-3"],
                "evidence_quotes": [{
                    "reference": "OPSINTEL.PIPELINE_LOGS · LOG-3",
                    "quote": "Processing ended before all expected rows were processed",
                }],
            }],
            "evidence_gaps": [],
        })
    }
    client = Mock()
    client.post.return_value = response

    result = summarize_investigation(INCIDENT, ROOT_CAUSES, client)

    assert result["status"] == "unavailable"
    assert result["claims"] == []


def test_llm_preserves_an_unresolved_outcome(monkeypatch):
    monkeypatch.setenv("OPSINTEL_LLM_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    unresolved_incident = {
        **INCIDENT,
        "category": "unclassified",
        "confidence": "low",
        "evidence": [{
            "type": "pipeline_log",
            "observation": "No recognizable failure signature was found",
            "source": "OPSINTEL.PIPELINE_LOGS",
            "log_id": 8,
        }],
    }
    unresolved_causes = {
        "candidates": [],
        "confirmed_root_cause": None,
        "resolution_status": "unresolved",
    }
    response = Mock()
    response.json.return_value = {
        "output_text": json.dumps({
            "claims": [{
                "statement": "The available evidence does not identify a cause.",
                "evidence_refs": ["OPSINTEL.PIPELINE_LOGS · LOG-8"],
                "evidence_quotes": [{
                    "reference": "OPSINTEL.PIPELINE_LOGS · LOG-8",
                    "quote": "No recognizable failure signature was found",
                }],
            }],
            "evidence_gaps": ["A diagnostic log with a recognizable failure signal"],
        })
    }
    client = Mock()
    client.post.return_value = response

    result = summarize_investigation(
        unresolved_incident,
        unresolved_causes,
        client,
    )

    assert result["status"] == "generated"
    assert "does not identify a cause" in result["summary"]
    assert unresolved_causes["confirmed_root_cause"] is None
