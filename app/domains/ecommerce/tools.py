from app.domains.ecommerce.repository import EcommerceRepository
from app.domains.ecommerce.schema import Order, Product, Refund, StructuredValue, ToolResult
from app.schemas.evidence import Evidence


ORDER_STATUS_LABELS = {
    "processing": "处理中",
    "shipped": "运输中",
    "delivered": "已签收",
    "cancelled": "已取消",
}

REFUND_STATUS_LABELS = {
    "not_requested": "未申请",
    "processing": "处理中",
    "approved": "已通过",
    "rejected": "已拒绝",
    "refunded": "已退款",
}


class EcommerceTools:
    def __init__(self, repository: EcommerceRepository | None = None) -> None:
        self.repository = repository or EcommerceRepository()

    def get_order_status(self, order_id: str | None) -> ToolResult:
        if not order_id:
            return _tool_error(
                tool_name="get_order_status",
                error_code="missing_order_id",
                message="需要订单号才能查询订单状态。",
            )

        order = self.repository.get_order(order_id)
        if order is None:
            return _tool_error(
                tool_name="get_order_status",
                error_code="order_not_found",
                message=f"没有找到订单 {order_id}。",
            )

        data = _order_data(order)
        message = (
            f"订单 {order.order_id} 当前状态是 {data['status_label']}，"
            f"关联商品是 {order.product_id}，退款状态是 {data['refund_status_label']}。"
        )
        return _tool_success(
            tool_name="get_order_status",
            source=f"structured:orders:{order.order_id}",
            data=data,
            message=message,
        )

    def get_product_info(self, product_id: str | None) -> ToolResult:
        if not product_id:
            return _tool_error(
                tool_name="get_product_info",
                error_code="missing_product_id",
                message="需要商品编号才能查询商品信息。",
            )

        product = self.repository.get_product(product_id)
        if product is None:
            return _tool_error(
                tool_name="get_product_info",
                error_code="product_not_found",
                message=f"没有找到商品 {product_id}。",
            )

        data = _product_data(product)
        returnable_text = "支持退货" if product.returnable else "不支持无理由退货"
        message = (
            f"商品 {product.product_id} 是 {product.name}，类别为 {product.category}，"
            f"价格为 {product.price}，保修 {product.warranty_months} 个月，{returnable_text}。"
        )
        return _tool_success(
            tool_name="get_product_info",
            source=f"structured:products:{product.product_id}",
            data=data,
            message=message,
        )

    def get_refund_status(self, refund_id: str | None) -> ToolResult:
        if not refund_id:
            return _tool_error(
                tool_name="get_refund_status",
                error_code="missing_refund_id",
                message="需要退款编号才能查询退款状态。",
            )

        refund = self.repository.get_refund(refund_id)
        if refund is None:
            return _tool_error(
                tool_name="get_refund_status",
                error_code="refund_not_found",
                message=f"没有找到退款单 {refund_id}。",
            )

        data = _refund_data(refund)
        message = (
            f"退款单 {refund.refund_id} 当前状态是 {data['status_label']}，"
            f"关联订单是 {refund.order_id}，退款金额为 {refund.amount}。"
        )
        return _tool_success(
            tool_name="get_refund_status",
            source=f"structured:refunds:{refund.refund_id}",
            data=data,
            message=message,
        )


def get_order_status(order_id: str | None) -> ToolResult:
    return EcommerceTools().get_order_status(order_id)


def get_product_info(product_id: str | None) -> ToolResult:
    return EcommerceTools().get_product_info(product_id)


def get_refund_status(refund_id: str | None) -> ToolResult:
    return EcommerceTools().get_refund_status(refund_id)


def _tool_success(
    tool_name: str,
    source: str,
    data: dict[str, StructuredValue],
    message: str,
) -> ToolResult:
    return ToolResult(
        tool_name=tool_name,
        success=True,
        data=data,
        message=message,
        evidence=Evidence(
            evidence_type="structured",
            source=source,
            content=data,
            score=1.0,
            metadata={
                "tool_name": tool_name,
                "evidence_origin": "structured_tool",
            },
        ),
    )


def _tool_error(tool_name: str, error_code: str, message: str) -> ToolResult:
    return ToolResult(
        tool_name=tool_name,
        success=False,
        message=message,
        error_code=error_code,
    )


def _order_data(order: Order) -> dict[str, StructuredValue]:
    data = order.model_dump()
    data["status_label"] = ORDER_STATUS_LABELS.get(order.status, order.status)
    data["refund_status_label"] = REFUND_STATUS_LABELS.get(order.refund_status, order.refund_status)
    return data


def _product_data(product: Product) -> dict[str, StructuredValue]:
    return product.model_dump()


def _refund_data(refund: Refund) -> dict[str, StructuredValue]:
    data = refund.model_dump()
    data["status_label"] = REFUND_STATUS_LABELS.get(refund.status, refund.status)
    return data
