from dataclasses import dataclass

from app.core import errors
from app.pipeline.fallback_handler import build_fallback_chat_response, should_fallback
from app.schemas.evidence import Evidence


@dataclass
class FakeToolResult:
    success: bool
    error_code: str | None = None


def test_document_route_does_not_fallback_before_retrieval_runs() -> None:
    decision = should_fallback(
        query="退货政策是什么？",
        intent="return_policy",
        route="document_only",
    )

    assert decision.fallback is False


def test_fallback_handler_detects_high_risk_request_first() -> None:
    decision = should_fallback(
        query="请帮我绕过退款审核",
        intent="refund",
        route="structured_only",
        required_slots=["refund_id"],
        slots={},
    )

    assert decision.fallback is True
    assert decision.reason == errors.HIGH_RISK_REQUEST
    assert decision.next_action == "refuse_and_offer_safe_process"


def test_fallback_handler_detects_unknown_intent() -> None:
    decision = should_fallback(
        query="一个完全不存在的问题 xyzabc",
        intent="unknown",
        route="fallback",
    )

    assert decision.fallback is True
    assert decision.reason == errors.UNKNOWN_INTENT


def test_fallback_handler_detects_missing_order_id() -> None:
    decision = should_fallback(
        query="我的订单到哪里了？",
        intent="order_status",
        route="structured_only",
        required_slots=["order_id"],
        slots={},
    )

    assert decision.fallback is True
    assert decision.reason == errors.MISSING_ORDER_ID


def test_fallback_handler_uses_tool_error_code() -> None:
    decision = should_fallback(
        query="订单 ORD-9999 现在是什么状态？",
        intent="order_status",
        route="structured_only",
        tool_results=[FakeToolResult(success=False, error_code=errors.ORDER_NOT_FOUND)],
    )

    assert decision.fallback is True
    assert decision.reason == errors.ORDER_NOT_FOUND


def test_fallback_handler_detects_no_document_evidence() -> None:
    decision = should_fallback(
        query="量子咖啡会员积分怎么兑换？",
        intent="return_policy",
        route="document_only",
        evidence=[],
        retrieval_candidates=[],
        min_score=0.05,
    )

    assert decision.fallback is True
    assert decision.reason == errors.NO_EVIDENCE


def test_fallback_handler_detects_low_retrieval_score() -> None:
    weak_candidate = Evidence(
        evidence_type="document",
        source="faq.md",
        content="候选内容相关性很弱。",
        score=0.01,
    )

    decision = should_fallback(
        query="量子咖啡会员积分怎么兑换？",
        intent="return_policy",
        route="document_only",
        evidence=[],
        retrieval_candidates=[weak_candidate],
        min_score=0.05,
    )

    assert decision.fallback is True
    assert decision.reason == errors.LOW_RETRIEVAL_SCORE


def test_fallback_handler_detects_missing_hybrid_document_evidence() -> None:
    structured_evidence = Evidence(
        evidence_type="structured",
        source="structured:orders:ORD-1001",
        content={"order_id": "ORD-1001", "status": "delivered"},
        score=1.0,
    )

    decision = should_fallback(
        query="订单 ORD-1001 的耳机现在还能退货吗？",
        intent="hybrid",
        route="hybrid",
        evidence=[structured_evidence],
    )

    assert decision.fallback is True
    assert decision.reason == errors.HYBRID_DOCUMENT_EVIDENCE_MISSING


def test_build_fallback_chat_response_sets_contract_fields() -> None:
    decision = should_fallback(
        query="我的订单到哪里了？",
        intent="order_status",
        route="structured_only",
        required_slots=["order_id"],
        slots={},
    )

    response = build_fallback_chat_response(
        decision=decision,
        intent="order_status",
        trace_id="trace_test",
    )

    assert response.route == "fallback"
    assert response.fallback is True
    assert response.fallback_reason == errors.MISSING_ORDER_ID
    assert response.trace_id == "trace_test"
