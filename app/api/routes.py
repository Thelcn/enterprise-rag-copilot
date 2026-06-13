from functools import lru_cache

from fastapi import APIRouter

from app.core.config import get_settings
from app.domains.ecommerce.adapter import (
    get_ecommerce_metadata_filter,
    get_ecommerce_intent_router,
    get_ecommerce_tools,
    load_ecommerce_documents,
)
from app.domains.ecommerce.schema import ToolResult
from app.pipeline.evidence_builder import build_evidence
from app.pipeline.intent_router import RouteDecision
from app.pipeline.rag_pipeline import RagPipeline
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.evidence import Evidence
from app.schemas.trace import new_trace_id


router = APIRouter()

# 进行健康度检查，返回服务状态和配置信息
@router.get("/health")
def health_check() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.service_name,
        "version": settings.service_version,
        "environment": settings.environment,
    }

# /chat 路由
@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    decision = get_ecommerce_intent_router().route(request.query)
    pipeline = get_chat_pipeline()

    if decision.route == "structured_only":
        return _run_structured_chat(decision)

    if decision.route == "hybrid":
        return _run_hybrid_chat(request=request, decision=decision, pipeline=pipeline)

    if decision.route == "fallback":
        return _fallback_response(
            intent=decision.intent,
            reason=decision.reason or "unknown_intent",
            message="我没有识别出这个问题需要查询哪类企业知识或业务数据。",
            evidence=[],
        )

    return pipeline.run_chat(
        query=request.query,
        user_id=request.user_id,
        session_id=request.session_id,
        intent=decision.intent,
        route=decision.route,
        metadata_filter=get_ecommerce_metadata_filter(decision.intent),
    )


@lru_cache
def get_chat_pipeline() -> RagPipeline:
    documents = load_ecommerce_documents()
    return RagPipeline.from_documents(documents, chunk_size=220, overlap=20)


def _run_structured_chat(decision: RouteDecision) -> ChatResponse:
    result = _run_tool_for_decision(decision)
    return _tool_result_to_chat_response(result=result, decision=decision)


def _run_hybrid_chat(
    request: ChatRequest,
    decision: RouteDecision,
    pipeline: RagPipeline,
) -> ChatResponse:
    order_result = get_ecommerce_tools().get_order_status(decision.slots.get("order_id"))
    if not order_result.success:
        return _tool_result_to_chat_response(result=order_result, decision=decision)

    document_response = pipeline.run_chat(
        query=request.query,
        user_id=request.user_id,
        session_id=request.session_id,
        intent=decision.intent,
        route="hybrid",
        metadata_filter=get_ecommerce_metadata_filter(decision.intent),
    )
    structured_evidence = build_evidence(tool_results=[order_result])
    if document_response.fallback:
        return _fallback_response(
            intent=decision.intent,
            reason="hybrid_document_evidence_missing",
            message="我找到了订单信息，但没有找到足够可靠的政策证据来判断这个具体问题。",
            evidence=structured_evidence,
            trace_id=document_response.trace_id,
        )

    evidence = build_evidence(
        tool_results=[order_result],
        retrieved_evidence=document_response.evidence,
    )
    return ChatResponse(
        answer=f"{order_result.message} 同时参考政策证据：{document_response.answer}",
        intent=decision.intent,
        route="hybrid",
        evidence=evidence,
        fallback=False,
        fallback_reason=None,
        trace_id=document_response.trace_id,
    )


def _run_tool_for_decision(decision: RouteDecision) -> ToolResult:
    tools = get_ecommerce_tools()
    if decision.intent == "order_status":
        return tools.get_order_status(decision.slots.get("order_id"))
    if decision.intent == "refund":
        return tools.get_refund_status(decision.slots.get("refund_id"))
    if decision.intent == "product_info":
        return tools.get_product_info(decision.slots.get("product_id"))
    return ToolResult(
        tool_name="unknown_structured_tool",
        success=False,
        error_code="unsupported_structured_intent",
        message=f"当前结构化工具不支持 intent={decision.intent}。",
    )


def _tool_result_to_chat_response(result: ToolResult, decision: RouteDecision) -> ChatResponse:
    trace_id = new_trace_id()
    evidence = build_evidence(tool_results=[result])
    if not result.success:
        return ChatResponse(
            answer=f"我无法从结构化业务数据中回答这个问题：{result.message}",
            intent=decision.intent,
            route="fallback",
            evidence=evidence,
            fallback=True,
            fallback_reason=result.error_code,
            trace_id=trace_id,
        )

    return ChatResponse(
        answer=result.message,
        intent=decision.intent,
        route=decision.route,
        evidence=evidence,
        fallback=False,
        fallback_reason=None,
        trace_id=trace_id,
    )


def _fallback_response(
    intent: str,
    reason: str,
    message: str,
    evidence: list[Evidence],
    trace_id: str | None = None,
) -> ChatResponse:
    return ChatResponse(
        answer=message,
        intent=intent,
        route="fallback",
        evidence=evidence,
        fallback=True,
        fallback_reason=reason,
        trace_id=trace_id or new_trace_id(),
    )
