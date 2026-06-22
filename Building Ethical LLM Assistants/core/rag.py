"""
RAG (Retrieval-Augmented Generation) stage runner.

Wraps the base assistant with retrieval over the knowledge base.
Teaching artifacts are dependency-injected so the notebook can pass
its own inline, editable versions into the same pipeline.
"""

from core.config import MOCK_MODE, DEFAULT_PROVIDER
from core.mocks import get_mock
from core.prompts import RAG_SYSTEM_PROMPT
from core.knowledge_base import KNOWLEDGE_BASE, retrieve_relevant_documents, format_retrieved_context
from core.logging import make_log_entry


def run_rag(
    message: str,
    provider_name: str | None = None,
    history: list[dict] | None = None,
    system_prompt: str | None = None,       # DI injection point
    knowledge_base: list[dict] | None = None,   # DI injection point
    retrieve_fn=None,                        # DI injection point
) -> dict:
    """
    Run the RAG-augmented assistant.

    Retrieval always runs (even in MOCK_MODE) so retrieval logs are
    instructive offline — participants can see which docs were retrieved
    even when the reply is canned.

    Returns:
        {reply, provider, model, mock, history, retrieval_log, log_entry}
    """
    provider_name = (provider_name or DEFAULT_PROVIDER).lower()
    system = system_prompt if system_prompt is not None else RAG_SYSTEM_PROMPT
    kb = knowledge_base if knowledge_base is not None else KNOWLEDGE_BASE
    retrieve = retrieve_fn if retrieve_fn is not None else retrieve_relevant_documents
    history = list(history) if history else []

    # Step 1: Retrieve relevant documents (runs in all modes — log is always real)
    retrieved_docs = retrieve(message, kb)
    retrieved_context = format_retrieved_context(retrieved_docs)

    retrieval_log = {
        "query": message,
        "retrieved_doc_ids": [d["id"] for d in retrieved_docs],
        "retrieved_doc_titles": [d["title"] for d in retrieved_docs],
    }

    if MOCK_MODE:
        reply = get_mock(message, "rag", provider_name)
        model = f"mock/{provider_name}"
        is_mock = True
    else:
        # Step 2: Build augmented message with retrieved context
        augmented_message = (
            f"USER QUESTION: {message}\n\n"
            f"RETRIEVED DOCUMENTS:\n{retrieved_context}\n\n"
            "Please answer the user's question based on the retrieved documents above.\n"
            "If the documents do not contain the information needed, say so clearly.\n"
        )
        from core.providers import get_provider
        provider = get_provider(provider_name)
        history.append({"role": "user", "content": augmented_message})
        reply = provider.complete(system, history)
        model = provider.model
        is_mock = False

    history.append({"role": "assistant", "content": reply})
    retrieval_log["response"] = reply

    log_entry = make_log_entry(
        query=message,
        provider=provider_name,
        model=model,
        mock=is_mock,
        stage="rag",
        retrieved_ids=retrieval_log["retrieved_doc_ids"],
        retrieved_titles=retrieval_log["retrieved_doc_titles"],
        response=reply,
    )

    return {
        "reply": reply,
        "provider": provider_name,
        "model": model,
        "mock": is_mock,
        "history": history,
        "retrieval_log": retrieval_log,
        "log_entry": log_entry,
    }
