from collections.abc import Iterable, Mapping
from typing import Protocol

from pydantic import BaseModel

from app.core import errors
from app.schemas.chat import ChatResponse
from app.schemas.evidence import Evidence
from app.schemas.trace import TraceInfo


class ToolResultLike(Protocol):
    success: bool
    error_code: str | None


class FallbackDecision(BaseModel):
    fallback: bool
    reason: str | None = None
    message: str | None = None
    next_action: str | None = None


FALLBACK_MESSAGES = {
    errors.UNKNOWN_INTENT: "我没有识别出这个问题需要查询哪类企业知识或业务数据。",
    errors.MISSING_ORDER_ID: "请提供订单号（例如 ORD-1001 或 EC1001），我才能查询订单状态或订单相关售后问题。",
    errors.MISSING_REFUND_ID: "请提供退款单号（例如 RF1001），我才能查询退款处理状态。",
    errors.MISSING_PRODUCT_ID: "请提供商品编号（例如 P-HEADPHONE-01），我才能查询商品信息。",
    errors.ORDER_NOT_FOUND: "我没有在当前结构化订单数据中找到这个订单，请检查订单号是否正确。",
    errors.REFUND_NOT_FOUND: "我没有在当前结构化退款数据中找到这个退款单，请检查退款单号是否正确。",
    errors.PRODUCT_NOT_FOUND: "我没有在当前结构化商品数据中找到这个商品，请检查商品编号是否正确。",
    errors.UNSUPPORTED_STRUCTURED_INTENT: "当前结构化工具还不支持这类业务查询。",
    errors.NO_EVIDENCE: "我没有在当前知识库中找到足够可靠的证据来回答这个问题。",
    errors.LOW_RETRIEVAL_SCORE: "我检索到的候选内容相关性过低，不能可靠回答这个问题。",
    errors.HIGH_RISK_REQUEST: "这个请求涉及绕过审核、规避规则或不当操作，我不能协助执行。可以帮你说明合规处理流程。",
    errors.HYBRID_DOCUMENT_EVIDENCE_MISSING: "我找到了结构化业务数据，但没有找到足够可靠的政策证据来判断这个具体问题。",
    errors.HYBRID_STRUCTURED_EVIDENCE_MISSING: "我找到了政策资料，但缺少必要的结构化业务数据来判断这个具体问题。",
}


NEXT_ACTIONS = {
    errors.MISSING_ORDER_ID: "ask_for_order_id",
    errors.MISSING_REFUND_ID: "ask_for_refund_id",
    errors.MISSING_PRODUCT_ID: "ask_for_product_id",
    errors.ORDER_NOT_FOUND: "verify_order_id",
    errors.REFUND_NOT_FOUND: "verify_refund_id",
    errors.PRODUCT_NOT_FOUND: "verify_product_id",
    errors.UNKNOWN_INTENT: "ask_clarifying_question",
    errors.NO_EVIDENCE: "handoff_or_expand_knowledge_base",
    errors.LOW_RETRIEVAL_SCORE: "handoff_or_refine_query",
    errors.HIGH_RISK_REQUEST: "refuse_and_offer_safe_process",
    errors.HYBRID_DOCUMENT_EVIDENCE_MISSING: "handoff_or_expand_policy_docs",
    errors.HYBRID_STRUCTURED_EVIDENCE_MISSING: "ask_for_required_business_id",
}


HIGH_RISK_TERMS = (
    "绕过",
    "规避",
    "伪造",
    "骗过",
    "跳过审核",
    "绕过审核",
    "强制退款",
    "破解",
    "篡改",
)


def should_fallback(
    *,
    query: str,
    intent: str,
    route: str,
    evidence: Iterable[Evidence] | None = None,
    tool_results: Iterable[ToolResultLike] | None = None,
    required_slots: Iterable[str] | None = None,
    slots: Mapping[str, str] | None = None,
    retrieval_candidates: Iterable[Evidence] | None = None,
    min_score: float | None = None,
) -> FallbackDecision:
    has_evidence_input = evidence is not None
    evidence_list = list(evidence or [])
    has_retrieval_candidates_input = retrieval_candidates is not None
    retrieval_candidate_list = list(retrieval_candidates or [])
    tool_result_list = list(tool_results or [])
    required_slot_list = list(required_slots or [])
    slot_map = dict(slots or {})

    if _is_high_risk_request(query):
        return _decision(errors.HIGH_RISK_REQUEST)

    if intent == "unknown" or route == "fallback":
        return _decision(errors.UNKNOWN_INTENT)

    missing_slot_reason = _missing_required_slot_reason(required_slot_list, slot_map)
    if missing_slot_reason is not None:
        return _decision(missing_slot_reason)

    for result in tool_result_list:
        if not result.success:
            return _decision(result.error_code or errors.UNSUPPORTED_STRUCTURED_INTENT)

    if route == "hybrid" and has_evidence_input:
        evidence_types = {item.evidence_type for item in evidence_list}
        if "structured" not in evidence_types:
            return _decision(errors.HYBRID_STRUCTURED_EVIDENCE_MISSING)
        if "document" not in evidence_types:
            return _decision(errors.HYBRID_DOCUMENT_EVIDENCE_MISSING)

    if _requires_evidence(route) and not evidence_list:
        if not has_evidence_input and not has_retrieval_candidates_input:
            return FallbackDecision(fallback=False)
        if min_score is not None and retrieval_candidate_list:
            return _decision(errors.LOW_RETRIEVAL_SCORE)
        return _decision(errors.NO_EVIDENCE)

    return FallbackDecision(fallback=False)


def build_fallback_chat_response(
    *,
    decision: FallbackDecision,
    intent: str,
    trace_id: str,
    evidence: list[Evidence] | None = None,
    trace: TraceInfo | None = None,
) -> ChatResponse:
    if not decision.fallback or decision.reason is None or decision.message is None:
        raise ValueError("fallback response requires a fallback decision with reason and message")

    return ChatResponse(
        answer=decision.message,
        intent=intent,
        route="fallback",
        evidence=evidence or [],
        fallback=True,
        fallback_reason=decision.reason,
        trace_id=trace_id,
        trace=trace,
    )


def _decision(reason: str) -> FallbackDecision:
    return FallbackDecision(
        fallback=True,
        reason=reason,
        message=FALLBACK_MESSAGES.get(reason, "我无法可靠回答这个问题。"),
        next_action=NEXT_ACTIONS.get(reason),
    )


def _is_high_risk_request(query: str) -> bool:
    normalized = query.strip().lower()
    return any(term in normalized for term in HIGH_RISK_TERMS)


def _missing_required_slot_reason(required_slots: list[str], slots: Mapping[str, str]) -> str | None:
    for slot in required_slots:
        if slots.get(slot):
            continue
        if slot == "order_id":
            return errors.MISSING_ORDER_ID
        if slot == "refund_id":
            return errors.MISSING_REFUND_ID
        if slot == "product_id":
            return errors.MISSING_PRODUCT_ID
    return None


def _requires_evidence(route: str) -> bool:
    return route in {"document_only", "hybrid"}
