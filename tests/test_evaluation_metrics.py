from app.schemas.evaluation import EvaluationCase
from evaluation.metrics import build_result, compute_metrics


def test_evaluation_metrics_counts_successful_case() -> None:
    case = EvaluationCase(
        id="S001",
        query="退货政策是什么？",
        expected_intent="return_policy",
        expected_route="document_only",
        required_evidence_keywords=["return_policy.md"],
        expected_fallback=False,
    )
    result = build_result(
        case,
        response_payload={
            "intent": "return_policy",
            "route": "document_only",
            "fallback": False,
            "fallback_reason": None,
            "trace_id": "trace_test",
            "trace": {"total_latency_ms": 1.2},
            "evidence": [{"source": "return_policy.md", "content": "退货政策"}],
        },
    )
    metrics = compute_metrics([result])

    assert result.passed is True
    assert metrics.total_cases == 1
    assert metrics.passed_cases == 1
    assert metrics.intent_accuracy == 1.0
    assert metrics.evidence_keyword_hit_rate == 1.0
    assert metrics.average_total_latency_ms == 1.2


def test_evaluation_metrics_records_failure_reason_mismatch() -> None:
    case = EvaluationCase(
        id="F001",
        query="我的订单到哪里了？",
        expected_intent="order_status",
        expected_route="fallback",
        expected_fallback=True,
        expected_fallback_reason="missing_order_id",
    )
    result = build_result(
        case,
        response_payload={
            "intent": "order_status",
            "route": "fallback",
            "fallback": True,
            "fallback_reason": "unknown_intent",
            "trace_id": "trace_test",
            "trace": {"total_latency_ms": 1.2},
            "evidence": [],
        },
    )
    metrics = compute_metrics([result])

    assert result.passed is False
    assert metrics.fallback_correctness == 1.0
    assert metrics.fallback_reason_accuracy == 0.0
