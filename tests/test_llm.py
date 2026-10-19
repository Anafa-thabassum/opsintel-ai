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
                                "statement": "Processing ended before completion.",
                                "evidence_refs": [
                                    "OPSINTEL.PIPELINE_LOGS · LOG-3"
                                ],
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
    assert result["summary"] == "Processing ended before completion."
    assert result["claims"] == [{
        "statement": "Processing ended before completion.",
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
