from pathlib import Path
from typing import Mapping

from app.schemas.document import MetadataValue


ECOMMERCE_POLICY_VERSION = "ecommerce-policy-2026-06"


ECOMMERCE_DOCUMENT_METADATA: dict[str, dict[str, MetadataValue]] = {
    "return_policy.md": {
        "domain": "ecommerce",
        "document_type": "return_policy",
        "product_category": "all",
        "policy_version": ECOMMERCE_POLICY_VERSION,
        "applicable_scenario": "return_request",
    },
    "logistics_policy.md": {
        "domain": "ecommerce",
        "document_type": "logistics_policy",
        "product_category": "all",
        "policy_version": ECOMMERCE_POLICY_VERSION,
        "applicable_scenario": "shipping_and_delivery",
    },
    "warranty_policy.md": {
        "domain": "ecommerce",
        "document_type": "warranty_policy",
        "product_category": "electronics",
        "policy_version": ECOMMERCE_POLICY_VERSION,
        "applicable_scenario": "warranty_repair",
    },
    "faq.md": {
        "domain": "ecommerce",
        "document_type": "faq",
        "product_category": "all",
        "policy_version": ECOMMERCE_POLICY_VERSION,
        "applicable_scenario": "after_sales_general",
    },
}


INTENT_METADATA_FILTERS: dict[str, dict[str, MetadataValue]] = {
    "return_policy": {"document_type": "return_policy"},
    "hybrid": {"document_type": "return_policy"},
    "logistics": {"document_type": "logistics_policy"},
    "warranty": {"document_type": "warranty_policy"},
}


REQUIRED_METADATA_KEYS = {
    "source",
    "path",
    "document_type",
    "product_category",
    "policy_version",
    "applicable_scenario",
}


def metadata_for_policy_document(file_path: str | Path) -> dict[str, MetadataValue]:
    path = Path(file_path)
    metadata = ECOMMERCE_DOCUMENT_METADATA.get(path.name)
    if metadata is None:
        return {
            "domain": "ecommerce",
            "document_type": "knowledge_base",
            "product_category": "all",
            "policy_version": ECOMMERCE_POLICY_VERSION,
            "applicable_scenario": "general",
        }
    return dict(metadata)


def metadata_filter_for_intent(intent: str) -> dict[str, MetadataValue] | None:
    metadata_filter = INTENT_METADATA_FILTERS.get(intent)
    if metadata_filter is None:
        return None
    return dict(metadata_filter)


def validate_required_metadata(metadata: Mapping[str, MetadataValue]) -> list[str]:
    return sorted(key for key in REQUIRED_METADATA_KEYS if key not in metadata)
