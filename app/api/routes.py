from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.trace import new_trace_id


router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.service_name,
        "version": settings.service_version,
        "environment": settings.environment,
    }


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    return ChatResponse(
        answer=(
            "This is a Day 2 mock response. The /chat API contract is ready, "
            "but retrieval and evidence-grounded generation are not connected yet."
        ),
        intent="mock_intent",
        evidence=[],
        fallback=True,
        fallback_reason="Day 2 mock mode: retrieval is not connected yet.",
        trace_id=new_trace_id(),
    )
