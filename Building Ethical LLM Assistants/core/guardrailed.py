"""
Guardrailed assistant runner.

Composes all five layers in sequence. Each layer is called by name
so participants can see the pipeline structure clearly.

Pipeline:
  1. validate_input       — block injection/out-of-scope pre-LLM [LLM01]
  2. retrieve             — RAG retrieval (same as RAG stage)
  3. model call           — via provider adapter
  4. filter_output        — scan reply for prohibited patterns [LLM09]
  5. compute_trust_score  — 0.0–1.0 heuristic [LLM09]
  6. should_escalate      — route to human on high-stakes signals [LLM06]
  7. make_log_entry       — structured audit trail [LLM02]
"""

from core.config import MOCK_MODE, DEFAULT_PROVIDER
from core.mocks import get_mock
from core.prompts import GUARDRAILED_SYSTEM_PROMPT, ESCALATION_RESPONSE, FALLBACK_RESPONSE
from core.knowledge_base import KNOWLEDGE_BASE, retrieve_relevant_documents, format_retrieved_context
from core.guardrails import validate_input, filter_output, should_escalate
from core.logging import make_log_entry


def run_guardrailed(
    message: str,
    provider_name: str | None = None,
    history: list[dict] | None = None,
    # ── Dependency-injection points (teaching artifacts) ──────────────────
    system_prompt: str | None = None,
    knowledge_base: list[dict] | None = None,
    retrieve_fn=None,
    validate_input_fn=None,
    filter_output_fn=None,
    should_escalate_fn=None,
    extra_output_rules_fn=None,   # for the type-one-guardrail exercise
) -> dict:
    """
    Run the guardrailed assistant (all five layers wrapping RAG).

    Returns:
        {reply, provider, model, mock, history, retrieval_log,
         guardrail_report, log_entry}
    """
    provider_name = (provider_name or DEFAULT_PROVIDER).lower()
    system = system_prompt if system_prompt is not None else GUARDRAILED_SYSTEM_PROMPT
    kb = knowledge_base if knowledge_base is not None else KNOWLEDGE_BASE
    retrieve = retrieve_fn if retrieve_fn is not None else retrieve_relevant_documents
    _validate = validate_input_fn if validate_input_fn is not None else validate_input
    _filter = filter_output_fn if filter_output_fn is not None else filter_output
    _escalate = should_escalate_fn if should_escalate_fn is not None else should_escalate
    history = list(history) if history else []

    # ── Layer 1: Input Validation ─────────────────────────────────────────
    input_result = _validate(message)

    if input_result["blocked"]:
        # Blocked pre-LLM — return immediately, no model call
        blocked_reply = (
            "I cannot process this request — it appears to contain instructions "
            "that attempt to override my guidelines. [LLM01: Prompt Injection blocked]"
        )
        log_entry = make_log_entry(
            query=message,
            provider=provider_name,
            model="blocked",
            mock=MOCK_MODE,
            stage="guardrails",
            input_flags=input_result["flags"],
            blocked_pre_llm=True,
            tokens_saved_estimated=input_result["tokens_saved_estimated"],
            response=blocked_reply,
        )
        guardrail_report = {
            "input_flags": input_result["flags"],
            "output_flags": [],
            "trust_score": 0.0,
            "trust_band": "blocked",
            "escalated": False,
            "blocked_pre_llm": True,
            "tokens_saved_estimated": input_result["tokens_saved_estimated"],
            "log_entry": log_entry,
        }
        return {
            "reply": blocked_reply,
            "provider": provider_name,
            "model": "blocked",
            "mock": MOCK_MODE,
            "history": history,
            "retrieval_log": None,
            "guardrail_report": guardrail_report,
            "log_entry": log_entry,
        }

    # ── Layer 2: Retrieval (RAG) ──────────────────────────────────────────
    retrieved_docs = retrieve(message, kb)
    retrieved_context = format_retrieved_context(retrieved_docs)
    retrieval_log = {
        "query": message,
        "retrieved_doc_ids": [d["id"] for d in retrieved_docs],
        "retrieved_doc_titles": [d["title"] for d in retrieved_docs],
    }

    # ── Layer 3: Model Call ───────────────────────────────────────────────
    if MOCK_MODE:
        raw_reply = get_mock(message, "guardrails", provider_name)
        model = f"mock/{provider_name}"
        is_mock = True
    else:
        augmented_message = (
            f"USER QUESTION: {message}\n\n"
            f"RETRIEVED DOCUMENTS:\n{retrieved_context}\n\n"
            "Please answer the user's question based on the retrieved documents above.\n"
            "If the documents do not contain the information needed, say so clearly.\n"
        )
        from core.providers import get_provider
        provider = get_provider(provider_name)
        history.append({"role": "user", "content": augmented_message})
        raw_reply = provider.complete(system, history)
        model = provider.model
        is_mock = False

    # ── Layer 4: Output Filtering ─────────────────────────────────────────
    output_result = _filter(raw_reply, retrieved_docs)
    output_flags = output_result["flags"]

    # Exercise: add participant's extra rule flags
    if extra_output_rules_fn is not None:
        extra_flags = extra_output_rules_fn(raw_reply)
        output_flags = list(set(output_flags + extra_flags))

    # ── Layer 4b: Trust Score ─────────────────────────────────────────────
    trust_score = output_result["trust_score"]

    if trust_score >= 0.7:
        trust_band = "pass"
    elif trust_score >= 0.4:
        trust_band = "fallback"
    else:
        trust_band = "escalate"

    # ── Layer 5: Human Escalation ─────────────────────────────────────────
    escalated = _escalate(message, trust_score)

    if escalated or trust_band == "escalate":
        final_reply = ESCALATION_RESPONSE
        escalated = True
    elif trust_band == "fallback":
        final_reply = FALLBACK_RESPONSE
    else:
        final_reply = raw_reply

    history.append({"role": "assistant", "content": final_reply})
    retrieval_log["response"] = final_reply

    # ── Layer 6 (implicit): Structured Logging ────────────────────────────
    log_entry = make_log_entry(
        query=message,
        provider=provider_name,
        model=model,
        mock=is_mock,
        stage="guardrails",
        retrieved_ids=retrieval_log["retrieved_doc_ids"],
        retrieved_titles=retrieval_log["retrieved_doc_titles"],
        input_flags=input_result["flags"],
        output_flags=output_flags,
        trust_score=trust_score,
        trust_band=trust_band,
        escalated=escalated,
        blocked_pre_llm=False,
        tokens_saved_estimated=0,
        response=final_reply,
    )

    guardrail_report = {
        "input_flags": input_result["flags"],
        "output_flags": output_flags,
        "trust_score": trust_score,
        "trust_band": trust_band,
        "escalated": escalated,
        "blocked_pre_llm": False,
        "tokens_saved_estimated": 0,
        "log_entry": log_entry,
    }

    return {
        "reply": final_reply,
        "provider": provider_name,
        "model": model,
        "mock": is_mock,
        "history": history,
        "retrieval_log": retrieval_log,
        "guardrail_report": guardrail_report,
        "log_entry": log_entry,
    }
