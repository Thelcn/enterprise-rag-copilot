from pathlib import Path
from functools import lru_cache
import re

from app.pipeline.document_loader import load_markdown_documents
from app.pipeline.intent_router import IntentRule, RuleBasedIntentRouter
from app.schemas.document import Document
from app.domains.ecommerce.repository import (
    EcommerceRepository,
    normalize_order_id,
    normalize_product_id,
    normalize_refund_id,
)
from app.domains.ecommerce.metadata_rules import (
    metadata_filter_for_intent,
    metadata_for_policy_document,
)
from app.domains.ecommerce.tools import EcommerceTools


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ECOMMERCE_DOCS_DIR = PROJECT_ROOT / "data" / "ecommerce" / "docs"
DEFAULT_ECOMMERCE_MOCK_DIR = PROJECT_ROOT / "data" / "ecommerce" / "mock"


def get_policy_doc_paths(data_dir: str | Path = DEFAULT_ECOMMERCE_DOCS_DIR) -> list[Path]:
    docs_dir = Path(data_dir)
    if not docs_dir.exists():
        raise FileNotFoundError(f"Ecommerce docs directory does not exist: {docs_dir}")
    return sorted(docs_dir.glob("*.md"))


def load_ecommerce_documents(data_dir: str | Path = DEFAULT_ECOMMERCE_DOCS_DIR) -> list[Document]:
    return load_markdown_documents(data_dir, metadata_provider=metadata_for_policy_document)


@lru_cache
def get_ecommerce_repository() -> EcommerceRepository:
    return EcommerceRepository(DEFAULT_ECOMMERCE_MOCK_DIR)


@lru_cache
def get_ecommerce_tools() -> EcommerceTools:
    return EcommerceTools(repository=get_ecommerce_repository())


@lru_cache
def get_ecommerce_intent_router() -> RuleBasedIntentRouter:
    return RuleBasedIntentRouter(
        rules=[
            IntentRule(
                intent="hybrid",
                route="hybrid",
                keywords=("可以退货", "能退货", "还能退", "退货吗", "七天无理由", "售后"),
                required_slots=("order_id",),
                any_slot=("order_id",),
                confidence=0.86,
                reason="query combines an order slot with return or after-sales policy terms",
            ),
            IntentRule(
                intent="refund",
                route="structured_only",
                keywords=("退款", "退费", "refund"),
                required_slots=("refund_id",),
                confidence=0.9,
                reason="refund status is a structured ecommerce fact",
            ),
            IntentRule(
                intent="order_status",
                route="structured_only",
                keywords=("订单", "状态", "到哪里", "发货", "送到", "物流进度"),
                required_slots=("order_id",),
                confidence=0.9,
                reason="order status is a structured ecommerce fact",
            ),
            IntentRule(
                intent="product_info",
                route="structured_only",
                keywords=("商品信息", "产品信息", "商品编号", "产品编号", "价格"),
                required_slots=("product_id",),
                confidence=0.88,
                reason="product facts are structured ecommerce data",
            ),
            IntentRule(
                intent="return_policy",
                route="document_only",
                keywords=("退货政策", "退货", "七天无理由", "无理由", "退换"),
                confidence=0.82,
                reason="return policy should be answered from policy documents",
            ),
            IntentRule(
                intent="warranty",
                route="document_only",
                keywords=("保修", "质保", "维修"),
                confidence=0.82,
                reason="warranty questions should be answered from policy documents",
            ),
            IntentRule(
                intent="logistics",
                route="document_only",
                keywords=("物流", "配送", "发货时间", "配送范围"),
                confidence=0.82,
                reason="logistics questions should be answered from policy documents",
            ),
        ],
        slot_patterns={
            "order_id": (
                re.compile(r"\b(?P<value>ORD-?\d{4}|EC\d{4})\b", re.IGNORECASE),
            ),
            "refund_id": (
                re.compile(r"\b(?P<value>RF-?\d{4})\b", re.IGNORECASE),
            ),
            "product_id": (
                re.compile(r"\b(?P<value>P-[A-Z0-9-]+)\b", re.IGNORECASE),
            ),
        },
        slot_normalizers={
            "order_id": normalize_order_id,
            "refund_id": normalize_refund_id,
            "product_id": normalize_product_id,
        },
    )


def get_ecommerce_metadata_filter(intent: str) -> dict[str, object] | None:
    return metadata_filter_for_intent(intent)
