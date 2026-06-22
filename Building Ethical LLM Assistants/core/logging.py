from datetime import datetime, timezone


def make_log_entry(**kwargs) -> dict:
    """
    Create a structured log entry for one assistant turn.
    All fields have safe defaults so callers only specify what they have.
    """
    return {
        "timestamp": kwargs.get("timestamp", datetime.now(timezone.utc).isoformat()),
        "query": kwargs.get("query", ""),
        "provider": kwargs.get("provider", ""),
        "model": kwargs.get("model", ""),
        "mock": kwargs.get("mock", False),
        "stage": kwargs.get("stage", "base"),
        "retrieved_ids": kwargs.get("retrieved_ids", []),
        "retrieved_titles": kwargs.get("retrieved_titles", []),
        "input_flags": kwargs.get("input_flags", []),
        "output_flags": kwargs.get("output_flags", []),
        "trust_score": kwargs.get("trust_score", None),
        "trust_band": kwargs.get("trust_band", None),
        "escalated": kwargs.get("escalated", False),
        "blocked_pre_llm": kwargs.get("blocked_pre_llm", False),
        "tokens_saved_estimated": kwargs.get("tokens_saved_estimated", 0),
        "response": kwargs.get("response", ""),
    }
