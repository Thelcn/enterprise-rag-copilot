from functools import lru_cache

from fastapi import APIRouter

from app.core import errors
from app.core.config import get_settings
from app.domains.ecommerce.adapter import (
    get_ecommerce_metadata_filter,
    get_ecommerce_intent_router,
    get_ecommerce_tools,
    load_ecommerce_documents,
)
from app.domains.ecommerce.schema import ToolResult
from app.pipeline.evidence_builder import build_evidence
from app.pipeline.fallback_handler import build_fallback_chat_response, should_fallback
from app.pipeline.intent_router import RouteDecision
from app.pipeline.performance_tracer import PerformanceTracer
from app.pipeline.rag_pipeline import RagPipeline
from app.schemas.chat import ChatRequest, ChatResponse


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
    tracer = PerformanceTracer()
    with tracer.span("intent"):
        decision = get_ecommerce_intent_router().route(request.query)

    fallback_decision = should_fallback(
        query=request.query,
        intent=decision.intent,
        route=decision.route,
        required_slots=decision.required_slots,
        slots=decision.slots,
    )
    if fallback_decision.fallback:
        with tracer.span("fallback", reason=fallback_decision.reason):
            response = build_fallback_chat_response(
                decision=fallback_decision,
                intent=decision.intent,
                trace_id=tracer.trace_id,
            )
        return _complete_response(response=response, tracer=tracer)

    if decision.route == "structured_only":
        return _run_structured_chat(decision=decision, tracer=tracer)

    pipeline = get_chat_pipeline()
    if decision.route == "hybrid":
        return _run_hybrid_chat(
            request=request,
            decision=decision,
            pipeline=pipeline,
            tracer=tracer,
        )

    response = pipeline.run_chat(
        query=request.query,
        user_id=request.user_id,
        session_id=request.session_id,
        intent=decision.intent,
        route=decision.route,
        metadata_filter=get_ecommerce_metadata_filter(decision.intent),
        tracer=tracer,
    )
    return _complete_response(response=response, tracer=tracer)


@lru_cache
def get_chat_pipeline() -> RagPipeline:
    documents = load_ecommerce_documents()
    return RagPipeline.from_documents(documents, chunk_size=220, overlap=20)


def _run_structured_chat(decision: RouteDecision, tracer: PerformanceTracer) -> ChatResponse:
    with tracer.span("tool", intent=decision.intent, tool_name=_tool_name_for_decision(decision)):
        result = _run_tool_for_decision(decision)
    response = _tool_result_to_chat_response(
        result=result,
        decision=decision,
        trace_id=tracer.trace_id,
    )
    return _complete_response(response=response, tracer=tracer)


def _run_hybrid_chat(
    request: ChatRequest,
    decision: RouteDecision,
    pipeline: RagPipeline,
    tracer: PerformanceTracer,
) -> ChatResponse:
    with tracer.span("tool", intent=decision.intent, tool_name="get_order_status"):
        order_result = get_ecommerce_tools().get_order_status(decision.slots.get("order_id"))
    if not order_result.success:
        response = _tool_result_to_chat_response(
            result=order_result,
            decision=decision,
            trace_id=tracer.trace_id,
        )
        return _complete_response(response=response, tracer=tracer)

    document_response = pipeline.run_chat(
        query=request.query,
        user_id=request.user_id,
        session_id=request.session_id,
        intent=decision.intent,
        route="hybrid",
        metadata_filter=get_ecommerce_metadata_filter(decision.intent),
        tracer=tracer,
    )
    structured_evidence = build_evidence(tool_results=[order_result])
    if document_response.fallback:
        fallback_decision = should_fallback(
            query=request.query,
            intent=decision.intent,
            route="hybrid",
            evidence=structured_evidence,
            tool_results=[order_result],
        )
        response = build_fallback_chat_response(
            decision=fallback_decision,
            intent=decision.intent,
            trace_id=document_response.trace_id,
            evidence=structured_evidence,
        )
        return _complete_response(response=response, tracer=tracer)

    evidence = build_evidence(
        tool_results=[order_result],
        retrieved_evidence=document_response.evidence,
    )
    fallback_decision = should_fallback(
        query=request.query,
        intent=decision.intent,
        route="hybrid",
        evidence=evidence,
        tool_results=[order_result],
    )
    if fallback_decision.fallback:
        response = build_fallback_chat_response(
            decision=fallback_decision,
            intent=decision.intent,
            trace_id=document_response.trace_id,
            evidence=evidence,
        )
        return _complete_response(response=response, tracer=tracer)

    response = ChatResponse(
        answer=f"{order_result.message} 同时参考政策证据：{document_response.answer}",
        intent=decision.intent,
        route="hybrid",
        evidence=evidence,
        fallback=False,
        fallback_reason=None,
        trace_id=document_response.trace_id,
    )
    return _complete_response(response=response, tracer=tracer)


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
        error_code=errors.UNSUPPORTED_STRUCTURED_INTENT,
        message=f"当前结构化工具不支持 intent={decision.intent}。",
    )


def _tool_result_to_chat_response(
    result: ToolResult,
    decision: RouteDecision,
    trace_id: str,
) -> ChatResponse:
    evidence = build_evidence(tool_results=[result])
    fallback_decision = should_fallback(
        query="",
        intent=decision.intent,
        route=decision.route,
        evidence=evidence,
        tool_results=[result],
    )
    if fallback_decision.fallback:
        return build_fallback_chat_response(
            decision=fallback_decision,
            intent=decision.intent,
            trace_id=trace_id,
            evidence=evidence,
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


def _tool_name_for_decision(decision: RouteDecision) -> str:
    if decision.intent == "order_status":
        return "get_order_status"
    if decision.intent == "refund":
        return "get_refund_status"
    if decision.intent == "product_info":
        return "get_product_info"
    return "unknown_structured_tool"


def _complete_response(response: ChatResponse, tracer: PerformanceTracer) -> ChatResponse:
    response.trace = tracer.finish()
    return response
