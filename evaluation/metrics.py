import json
from collections.abc import Mapping, Sequence
from typing import Any

from app.schemas.evaluation import EvaluationCase, EvaluationMetrics, EvaluationResult


def build_result(
    case: EvaluationCase,
    response_payload: Mapping[str, Any] | None = None,
    error: str | None = None,
) -> EvaluationResult:
    if error is not None or response_payload is None:
        return EvaluationResult(
            case_id=case.id,
            query=case.query,
            expected_intent=case.expected_intent,
            expected_route=case.expected_route,
            expected_fallback=case.expected_fallback,
            expected_fallback_reason=case.expected_fallback_reason,
            required_evidence_keywords=case.required_evidence_keywords,
            error=error or "No response payload returned.",
            passed=False,
        )

    evidence = response_payload.get("evidence") or []
    trace = response_payload.get("trace") or {}
    total_latency_ms = trace.get("total_latency_ms") if isinstance(trace, Mapping) else None
    evidence_keyword_hit = _evidence_keyword_hit(evidence, case.required_evidence_keywords)

    actual_intent = response_payload.get("intent")
    actual_route = response_payload.get("route")
    actual_fallback = response_payload.get("fallback")
    actual_fallback_reason = response_payload.get("fallback_reason")
    checks = [
        actual_intent == case.expected_intent,
        actual_route == case.expected_route,
        actual_fallback == case.expected_fallback,
    ]
    if case.expected_fallback_reason is not None:
        checks.append(actual_fallback_reason == case.expected_fallback_reason)
    if case.required_evidence_keywords:
        checks.append(evidence_keyword_hit is True)

    return EvaluationResult(
        case_id=case.id,
        query=case.query,
        expected_intent=case.expected_intent,
        actual_intent=actual_intent,
        expected_route=case.expected_route,
        actual_route=actual_route,
        expected_fallback=case.expected_fallback,
        actual_fallback=actual_fallback,
        expected_fallback_reason=case.expected_fallback_reason,
        actual_fallback_reason=actual_fallback_reason,
        required_evidence_keywords=case.required_evidence_keywords,
        evidence_count=len(evidence),
        evidence_keyword_hit=evidence_keyword_hit,
        evidence_present=bool(evidence),
        trace_id=response_payload.get("trace_id"),
        total_latency_ms=total_latency_ms if isinstance(total_latency_ms, (int, float)) else None,
        passed=all(checks),
    )


def compute_metrics(results: Sequence[EvaluationResult]) -> EvaluationMetrics:
    total_cases = len(results)
    passed_cases = sum(1 for result in results if result.passed)
    expected_non_fallback = [result for result in results if result.expected_fallback is False]
    keyword_results = [
        result
        for result in results
        if result.required_evidence_keywords and result.evidence_keyword_hit is not None
    ]
    fallback_reason_results = [
        result
        for result in results
        if result.expected_fallback_reason is not None
    ]
    latency_values = [
        result.total_latency_ms
        for result in results
        if result.total_latency_ms is not None
    ]

    return EvaluationMetrics(
        total_cases=total_cases,
        passed_cases=passed_cases,
        intent_accuracy=_rate(result.actual_intent == result.expected_intent for result in results),
        route_accuracy=_rate(result.actual_route == result.expected_route for result in results),
        fallback_correctness=_rate(result.actual_fallback == result.expected_fallback for result in results),
        fallback_reason_accuracy=_optional_rate(
            result.actual_fallback_reason == result.expected_fallback_reason
            for result in fallback_reason_results
        ),
        evidence_presence_rate=_rate(result.evidence_present for result in expected_non_fallback),
        evidence_keyword_hit_rate=_optional_rate(result.evidence_keyword_hit is True for result in keyword_results),
        error_count=sum(1 for result in results if result.error is not None),
        average_total_latency_ms=round(sum(latency_values) / len(latency_values), 4)
        if latency_values
        else None,
    )


def _evidence_keyword_hit(evidence: object, required_keywords: list[str]) -> bool | None:
    if not required_keywords:
        return None
    searchable = json.dumps(evidence, ensure_ascii=False, sort_keys=True)
    return all(keyword in searchable for keyword in required_keywords)


def _rate(values: Sequence[bool] | object) -> float:
    value_list = list(values)
    if not value_list:
        return 0.0
    return round(sum(1 for value in value_list if value) / len(value_list), 4)


def _optional_rate(values: Sequence[bool] | object) -> float | None:
    value_list = list(values)
    if not value_list:
        return None
    return _rate(value_list)
