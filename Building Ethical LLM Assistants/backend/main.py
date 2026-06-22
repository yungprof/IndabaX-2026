from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.runner import run_base
from core.rag import run_rag
from core.guardrailed import run_guardrailed
from core.observability import summarize_logs

app = FastAPI(title="LLM Assistants Demo API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Local demo only — tighten for production
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session log — accumulated across requests for /observability
_session_log: list[dict] = []


class ChatRequest(BaseModel):
    mode: str
    message: str
    provider: str = "anthropic"


class ChatResponse(BaseModel):
    reply: str
    provider: str
    model: str
    mock: bool
    retrieval_log: dict | None = None
    guardrail_report: dict | None = None


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    if request.mode == "base":
        result = run_base(
            message=request.message,
            provider_name=request.provider,
        )
        _session_log.append(result["log_entry"])
        return ChatResponse(
            reply=result["reply"],
            provider=result["provider"],
            model=result["model"],
            mock=result["mock"],
            retrieval_log=None,
            guardrail_report=None,
        )

    if request.mode == "rag":
        result = run_rag(
            message=request.message,
            provider_name=request.provider,
        )
        _session_log.append(result["log_entry"])
        return ChatResponse(
            reply=result["reply"],
            provider=result["provider"],
            model=result["model"],
            mock=result["mock"],
            retrieval_log=result["retrieval_log"],
            guardrail_report=None,
        )

    if request.mode == "guardrails":
        result = run_guardrailed(
            message=request.message,
            provider_name=request.provider,
        )
        _session_log.append(result["log_entry"])
        return ChatResponse(
            reply=result["reply"],
            provider=result["provider"],
            model=result["model"],
            mock=result["mock"],
            retrieval_log=result["retrieval_log"],
            guardrail_report=result["guardrail_report"],
        )

    raise HTTPException(status_code=400, detail=f"Unknown mode: {request.mode!r}")


@app.get("/observability")
def observability() -> dict:
    return summarize_logs(_session_log)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
