from functools import lru_cache

from fastapi import APIRouter

from app.core.config import get_settings
from app.domains.ecommerce.adapter import load_ecommerce_documents
from app.pipeline.rag_pipeline import RagPipeline
from app.schemas.chat import ChatRequest, ChatResponse


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
    pipeline = get_chat_pipeline()
    return pipeline.run_chat(
        query=request.query,
        user_id=request.user_id,
        session_id=request.session_id,
    )


@lru_cache
def get_chat_pipeline() -> RagPipeline:
    documents = load_ecommerce_documents()
    return RagPipeline.from_documents(documents, chunk_size=220, overlap=20)
