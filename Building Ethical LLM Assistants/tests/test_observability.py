"""
Tests for the observability dashboard (summarize_logs).
"""
import os
os.environ["MOCK_MODE"] = "true"

from core.observability import summarize_logs
from core.logging import make_log_entry
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def _make_entry(**kwargs):
    return make_log_entry(**kwargs)


def test_empty_log_returns_zeros():
    result = summarize_logs([])
    assert result["total_requests"] == 0
    assert result["flagged_count"] == 0
    assert result["blocked_pre_llm_count"] == 0
    assert result["total_tokens_saved_estimated"] == 0
    assert result["violation_taxonomy"] == {}


def test_counts_flagged_interactions():
    logs = [
        _make_entry(input_flags=["injection_attempt"], blocked_pre_llm=True, tokens_saved_estimated=20),
        _make_entry(output_flags=["guarantee"]),
        _make_entry(),  # clean
    ]
    result = summarize_logs(logs)
    assert result["total_requests"] == 3
    assert result["flagged_count"] == 2
    assert result["blocked_pre_llm_count"] == 1
    assert result["total_tokens_saved_estimated"] == 20


def test_violation_taxonomy_counts_by_type():
    logs = [
        _make_entry(input_flags=["injection_attempt"]),
        _make_entry(output_flags=["guarantee"]),
        _make_entry(output_flags=["guarantee"]),
        _make_entry(output_flags=["final_decision"]),
    ]
    result = summarize_logs(logs)
    taxonomy = result["violation_taxonomy"]
    assert taxonomy.get("injection_attempt") == 1
    assert taxonomy.get("guarantee") == 2
    assert taxonomy.get("final_decision") == 1


def test_mock_mode_sets_caveat():
    logs = [_make_entry(mock=True)]
    result = summarize_logs(logs)
    assert result["mock_mode"] is True
    assert "illustrative" in result["caveat"]
    assert "MOCK" in result["caveat"]


def test_live_mode_caveat_says_estimated_only():
    logs = [_make_entry(mock=False)]
    result = summarize_logs(logs)
    assert result["mock_mode"] is False
    assert result["caveat"] == "estimated"


def test_escalated_appears_in_taxonomy():
    logs = [_make_entry(escalated=True)]
    result = summarize_logs(logs)
    assert result["violation_taxonomy"].get("escalated") == 1


def test_observability_endpoint():
    # Hit the chat endpoint to populate the session log
    client.post("/chat", json={
        "mode": "base", "message": "hello", "provider": "anthropic"
    })
    resp = client.get("/observability")
    assert resp.status_code == 200
    data = resp.json()
    required = ["total_requests", "flagged_count", "blocked_pre_llm_count",
                "violation_taxonomy", "total_tokens_saved_estimated", "caveat"]
    for key in required:
        assert key in data
