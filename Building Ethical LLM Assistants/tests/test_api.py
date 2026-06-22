"""
Integration tests for the FastAPI /chat endpoint. All run in MOCK_MODE.
"""
import os
os.environ["MOCK_MODE"] = "true"

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

REQUIRED_ENVELOPE_KEYS = {"reply", "provider", "model", "mock", "retrieval_log", "guardrail_report"}


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_chat_base_mode_returns_valid_envelope():
    resp = client.post("/chat", json={
        "mode": "base",
        "message": "I am a market trader in Kumasi, can I get a loan without a payslip?",
        "provider": "anthropic",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert REQUIRED_ENVELOPE_KEYS.issubset(data.keys())
    assert len(data["reply"]) > 0
    assert data["mock"] is True
    assert data["retrieval_log"] is None
    assert data["guardrail_report"] is None


def test_chat_base_mode_gemma_provider():
    resp = client.post("/chat", json={
        "mode": "base",
        "message": "Me I no sabi plenty English, help me small",
        "provider": "gemma",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "gemma"
    assert len(data["reply"]) > 0


def test_chat_rag_mode_returns_200_with_retrieval_log():
    resp = client.post("/chat", json={
        "mode": "rag",
        "message": "Is it legal for a lender to charge me hidden fees?",
        "provider": "anthropic",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["retrieval_log"] is not None


def test_chat_guardrails_mode_returns_200_with_report():
    resp = client.post("/chat", json={
        "mode": "guardrails",
        "message": "Is it legal for a lender to charge me hidden fees?",
        "provider": "anthropic",
    })
    assert resp.status_code == 200
    assert resp.json()["guardrail_report"] is not None


def test_chat_unknown_mode_returns_400():
    resp = client.post("/chat", json={
        "mode": "unknown",
        "message": "test",
        "provider": "anthropic",
    })
    assert resp.status_code == 400
