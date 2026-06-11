from pydantic import BaseModel, Field

from app.schemas.evidence import Evidence


StructuredValue = str | int | float | bool | None


class Order(BaseModel):
    order_id: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)
    product_id: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    created_at: str = Field(..., min_length=1)
    refund_status: str = Field(..., min_length=1)


class Product(BaseModel):
    product_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    price: float = Field(..., ge=0.0)
    warranty_months: int = Field(..., ge=0)
    returnable: bool


class Refund(BaseModel):
    refund_id: str = Field(..., min_length=1)
    order_id: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    amount: float = Field(..., ge=0.0)
    requested_at: str = Field(..., min_length=1)
    updated_at: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)


class ToolResult(BaseModel):
    tool_name: str = Field(..., min_length=1)
    success: bool
    message: str
    data: dict[str, StructuredValue] = Field(default_factory=dict)
    evidence: Evidence | None = None
    error_code: str | None = None
