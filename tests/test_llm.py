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
                            "summary": "The run ended with 20 rows missing.",
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
    assert result["evidence_gaps"] == ["The first termination error"]
    request = client.post.call_args.kwargs
    assert request["json"]["store"] is False
    assert request["json"]["text"]["format"]["strict"] is True
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
