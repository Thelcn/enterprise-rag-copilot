import json
import re
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from app.domains.ecommerce.schema import Order, Product, Refund


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ECOMMERCE_MOCK_DIR = PROJECT_ROOT / "data" / "ecommerce" / "mock"

ModelT = TypeVar("ModelT", bound=BaseModel)


class EcommerceRepository:
    def __init__(self, data_dir: str | Path = DEFAULT_ECOMMERCE_MOCK_DIR) -> None:
        self.data_dir = Path(data_dir)
        self._orders: dict[str, Order] | None = None
        self._products: dict[str, Product] | None = None
        self._refunds: dict[str, Refund] | None = None

    @property
    def orders(self) -> dict[str, Order]:
        if self._orders is None:
            records = _load_records(self.data_dir / "orders.json", Order)
            self._orders = {record.order_id: record for record in records}
        return self._orders

    @property
    def products(self) -> dict[str, Product]:
        if self._products is None:
            records = _load_records(self.data_dir / "products.json", Product)
            self._products = {record.product_id: record for record in records}
        return self._products

    @property
    def refunds(self) -> dict[str, Refund]:
        if self._refunds is None:
            records = _load_records(self.data_dir / "refunds.json", Refund)
            self._refunds = {record.refund_id: record for record in records}
        return self._refunds

    def get_order(self, order_id: str | None) -> Order | None:
        if not order_id:
            return None
        return self.orders.get(normalize_order_id(order_id))

    def get_product(self, product_id: str | None) -> Product | None:
        if not product_id:
            return None
        return self.products.get(normalize_product_id(product_id))

    def get_refund(self, refund_id: str | None) -> Refund | None:
        if not refund_id:
            return None
        return self.refunds.get(normalize_refund_id(refund_id))


def normalize_order_id(order_id: str) -> str:
    value = order_id.strip().upper().replace(" ", "")
    if re.fullmatch(r"ORD\d{4}", value):
        return f"ORD-{value[3:]}"
    if re.fullmatch(r"EC\d{4}", value):
        return f"ORD-{value[2:]}"
    return value


def normalize_product_id(product_id: str) -> str:
    return product_id.strip().upper()


def normalize_refund_id(refund_id: str) -> str:
    return refund_id.strip().upper().replace("-", "")


def _load_records(path: Path, model_type: type[ModelT]) -> list[ModelT]:
    if not path.exists():
        raise FileNotFoundError(f"Ecommerce mock data file does not exist: {path}")

    raw_records = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw_records, list):
        raise ValueError(f"Ecommerce mock data file must contain a JSON list: {path}")

    return [model_type.model_validate(record) for record in raw_records]
