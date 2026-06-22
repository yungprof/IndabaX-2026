"""
Runner functions for the three assistant stages.
Each accepts teaching artifacts via dependency injection so the notebook
can pass its own inline, editable versions into the same pipeline.
"""

from core.config import MOCK_MODE, DEFAULT_PROVIDER
from core.mocks import get_mock
from core.prompts import BASE_SYSTEM_PROMPT
from core.logging import make_log_entry


def run_base(
    message: str,
    provider_name: str | None = None,
    history: list[dict] | None = None,
    system_prompt: str | None = None,  # DI injection point
) -> dict:
    """
    Run the base assistant (system prompt + provider, no retrieval, no guardrails).

    Returns:
        {reply, provider, model, mock, history, log_entry}
    """
    provider_name = (provider_name or DEFAULT_PROVIDER).lower()
    system = system_prompt if system_prompt is not None else BASE_SYSTEM_PROMPT
    history = list(history) if history else []

    if MOCK_MODE:
        reply = get_mock(message, "base", provider_name)
        model = f"mock/{provider_name}"
        is_mock = True
    else:
        from core.providers import get_provider
        provider = get_provider(provider_name)
        history.append({"role": "user", "content": message})
        reply = provider.complete(system, history)
        model = provider.model
        is_mock = False

    history.append({"role": "assistant", "content": reply})

    log_entry = make_log_entry(
        query=message,
        provider=provider_name,
        model=model,
        mock=is_mock,
        stage="base",
        response=reply,
    )

    return {
        "reply": reply,
        "provider": provider_name,
        "model": model,
        "mock": is_mock,
        "history": history,
        "log_entry": log_entry,
    }
