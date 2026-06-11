from app.domains.ecommerce.repository import EcommerceRepository
from app.domains.ecommerce.tools import EcommerceTools


def test_get_order_status_returns_structured_evidence() -> None:
    tools = EcommerceTools(repository=EcommerceRepository())

    result = tools.get_order_status("ORD-1001")

    assert result.success is True
    assert result.error_code is None
    assert result.data["order_id"] == "ORD-1001"
    assert result.data["status"] == "delivered"
    assert result.evidence is not None
    assert result.evidence.source == "structured:orders:ORD-1001"
    assert result.evidence.score == 1.0


def test_get_order_status_supports_ec_alias() -> None:
    tools = EcommerceTools(repository=EcommerceRepository())

    result = tools.get_order_status("EC1001")

    assert result.success is True
    assert result.data["order_id"] == "ORD-1001"


def test_get_order_status_reports_missing_order_id() -> None:
    tools = EcommerceTools(repository=EcommerceRepository())

    result = tools.get_order_status(None)

    assert result.success is False
    assert result.error_code == "missing_order_id"
    assert result.evidence is None


def test_get_order_status_reports_not_found() -> None:
    tools = EcommerceTools(repository=EcommerceRepository())

    result = tools.get_order_status("ORD-9999")

    assert result.success is False
    assert result.error_code == "order_not_found"


def test_get_product_info_returns_structured_evidence() -> None:
    tools = EcommerceTools(repository=EcommerceRepository())

    result = tools.get_product_info("P-HEADPHONE-01")

    assert result.success is True
    assert result.data["product_id"] == "P-HEADPHONE-01"
    assert result.data["returnable"] is True
    assert result.evidence is not None
    assert result.evidence.source == "structured:products:P-HEADPHONE-01"


def test_get_refund_status_returns_structured_evidence() -> None:
    tools = EcommerceTools(repository=EcommerceRepository())

    result = tools.get_refund_status("RF1001")

    assert result.success is True
    assert result.data["refund_id"] == "RF1001"
    assert result.data["status"] == "approved"
    assert result.evidence is not None
    assert result.evidence.source == "structured:refunds:RF1001"


def test_get_refund_status_reports_not_found() -> None:
    tools = EcommerceTools(repository=EcommerceRepository())

    result = tools.get_refund_status("RF9999")

    assert result.success is False
    assert result.error_code == "refund_not_found"
