from app.domains.ecommerce.adapter import load_ecommerce_documents
from app.domains.ecommerce.metadata_rules import (
    ECOMMERCE_POLICY_VERSION,
    metadata_filter_for_intent,
    metadata_for_policy_document,
    validate_required_metadata,
)


def test_metadata_rules_define_policy_document_types() -> None:
    assert metadata_for_policy_document("return_policy.md")["document_type"] == "return_policy"
    assert metadata_for_policy_document("logistics_policy.md")["document_type"] == "logistics_policy"
    assert metadata_for_policy_document("warranty_policy.md")["document_type"] == "warranty_policy"
    assert metadata_for_policy_document("faq.md")["document_type"] == "faq"


def test_metadata_rules_include_version_and_scenario() -> None:
    metadata = metadata_for_policy_document("warranty_policy.md")

    assert metadata["policy_version"] == ECOMMERCE_POLICY_VERSION
    assert metadata["product_category"] == "electronics"
    assert metadata["applicable_scenario"] == "warranty_repair"


def test_metadata_filter_for_intent_maps_policy_intents() -> None:
    assert metadata_filter_for_intent("return_policy") == {"document_type": "return_policy"}
    assert metadata_filter_for_intent("hybrid") == {"document_type": "return_policy"}
    assert metadata_filter_for_intent("logistics") == {"document_type": "logistics_policy"}
    assert metadata_filter_for_intent("warranty") == {"document_type": "warranty_policy"}
    assert metadata_filter_for_intent("order_status") is None


def test_loaded_ecommerce_documents_have_required_metadata() -> None:
    documents = load_ecommerce_documents()

    assert documents
    for document in documents:
        assert validate_required_metadata(document.metadata) == []
        assert document.metadata["policy_version"] == ECOMMERCE_POLICY_VERSION
