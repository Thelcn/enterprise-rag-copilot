from app.domains.ecommerce.adapter import get_ecommerce_intent_router


def test_router_detects_order_status_intent() -> None:
    decision = get_ecommerce_intent_router().route("我的订单 ORD-1001 现在是什么状态？")

    assert decision.intent == "order_status"
    assert decision.route == "structured_only"
    assert decision.required_slots == ["order_id"]
    assert decision.slots["order_id"] == "ORD-1001"


def test_router_normalizes_ec_order_alias() -> None:
    decision = get_ecommerce_intent_router().route("我的订单 EC1001 现在是什么状态？")

    assert decision.intent == "order_status"
    assert decision.slots["order_id"] == "ORD-1001"


def test_router_detects_refund_intent() -> None:
    decision = get_ecommerce_intent_router().route("退款 RF1001 处理到哪一步了？")

    assert decision.intent == "refund"
    assert decision.route == "structured_only"
    assert decision.required_slots == ["refund_id"]
    assert decision.slots["refund_id"] == "RF1001"


def test_router_detects_return_policy_intent() -> None:
    decision = get_ecommerce_intent_router().route("退货政策是什么？")

    assert decision.intent == "return_policy"
    assert decision.route == "document_only"


def test_router_detects_warranty_intent() -> None:
    decision = get_ecommerce_intent_router().route("保修范围是什么？")

    assert decision.intent == "warranty"
    assert decision.route == "document_only"


def test_router_detects_logistics_intent() -> None:
    decision = get_ecommerce_intent_router().route("配送范围有哪些限制？")

    assert decision.intent == "logistics"
    assert decision.route == "document_only"


def test_router_detects_hybrid_intent() -> None:
    decision = get_ecommerce_intent_router().route("订单 ORD-1001 的耳机现在还能退货吗？")

    assert decision.intent == "hybrid"
    assert decision.route == "hybrid"
    assert decision.required_slots == ["order_id"]
    assert decision.slots["order_id"] == "ORD-1001"


def test_router_fallbacks_on_unknown_intent() -> None:
    decision = get_ecommerce_intent_router().route("量子咖啡会员积分怎么兑换？")

    assert decision.intent == "unknown"
    assert decision.route == "fallback"
    assert decision.reason == "no_intent_matched"
