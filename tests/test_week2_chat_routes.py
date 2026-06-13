from fastapi.testclient import TestClient

from app.core import errors
from app.main import app


client = TestClient(app)


def test_chat_routes_order_status_to_structured_tool() -> None:
    response = client.post(
        "/chat",
        json={
            "user_id": "demo_user_001",
            "session_id": "week2-day2",
            "query": "我的订单 ORD-1001 现在是什么状态？",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "order_status"
    assert payload["route"] == "structured_only"
    assert payload["fallback"] is False
    assert payload["evidence"]
    assert payload["evidence"][0]["source"] == "structured:orders:ORD-1001"
    assert payload["evidence"][0]["evidence_type"] == "structured"
    assert payload["evidence"][0]["content"]["order_id"] == "ORD-1001"
    assert "ORD-1001" in payload["answer"]


def test_chat_routes_refund_status_to_structured_tool() -> None:
    response = client.post(
        "/chat",
        json={
            "user_id": "demo_user_002",
            "session_id": "week2-day2",
            "query": "退款 RF1001 处理到哪一步了？",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "refund"
    assert payload["route"] == "structured_only"
    assert payload["fallback"] is False
    assert payload["evidence"][0]["source"] == "structured:refunds:RF1001"
    assert payload["evidence"][0]["evidence_type"] == "structured"


def test_chat_fallbacks_when_order_id_is_missing() -> None:
    response = client.post(
        "/chat",
        json={
            "user_id": "demo_user_001",
            "session_id": "week2-day2",
            "query": "我的订单现在是什么状态？",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "order_status"
    assert payload["route"] == "fallback"
    assert payload["fallback"] is True
    assert payload["fallback_reason"] == errors.MISSING_ORDER_ID


def test_chat_fallbacks_when_order_is_not_found() -> None:
    response = client.post(
        "/chat",
        json={
            "user_id": "demo_user_001",
            "session_id": "week2-day5",
            "query": "订单 ORD-9999 现在是什么状态？",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "order_status"
    assert payload["route"] == "fallback"
    assert payload["fallback"] is True
    assert payload["fallback_reason"] == errors.ORDER_NOT_FOUND


def test_chat_fallbacks_for_high_risk_request() -> None:
    response = client.post(
        "/chat",
        json={
            "user_id": "demo_user_001",
            "session_id": "week2-day5",
            "query": "请帮我绕过退款审核",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["route"] == "fallback"
    assert payload["fallback"] is True
    assert payload["fallback_reason"] == errors.HIGH_RISK_REQUEST


def test_chat_fallbacks_for_unknown_intent() -> None:
    response = client.post(
        "/chat",
        json={
            "user_id": "demo_user_001",
            "session_id": "week2-day5",
            "query": "一个完全不存在的问题 xyzabc",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "unknown"
    assert payload["route"] == "fallback"
    assert payload["fallback"] is True
    assert payload["fallback_reason"] == errors.UNKNOWN_INTENT


def test_chat_fallbacks_when_product_id_is_missing() -> None:
    response = client.post(
        "/chat",
        json={
            "user_id": "demo_user_001",
            "session_id": "week2-day5",
            "query": "商品价格是多少？",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "product_info"
    assert payload["route"] == "fallback"
    assert payload["fallback"] is True
    assert payload["fallback_reason"] == errors.MISSING_PRODUCT_ID


def test_chat_keeps_policy_questions_on_document_route() -> None:
    response = client.post(
        "/chat",
        json={
            "user_id": "demo_user_001",
            "session_id": "week2-day2",
            "query": "退货政策是什么？",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "return_policy"
    assert payload["route"] == "document_only"
    assert payload["fallback"] is False
    assert payload["evidence"][0]["source"] == "return_policy.md"
    assert payload["evidence"][0]["evidence_type"] == "document"
