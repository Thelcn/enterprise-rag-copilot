import json
from pathlib import Path

import pytest

from app.domains.ecommerce.adapter import (
    DEFAULT_ECOMMERCE_DOCS_DIR,
    get_policy_doc_paths,
    load_ecommerce_documents,
)
from app.pipeline.document_loader import load_markdown_documents


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_load_ecommerce_policy_documents() -> None:
    documents = load_ecommerce_documents()

    assert len(documents) == 4
    assert {document.source for document in documents} == {
        "faq.md",
        "return_policy.md",
        "logistics_policy.md",
        "warranty_policy.md",
    }

    for document in documents:
        assert document.id.startswith("doc_")
        assert document.content
        assert document.metadata["source"] == document.source
        assert document.metadata["document_type"] == Path(document.source).stem
        assert document.metadata["file_extension"] == ".md"


def test_get_policy_doc_paths_returns_markdown_files() -> None:
    paths = get_policy_doc_paths()

    assert len(paths) == 4
    assert all(path.suffix == ".md" for path in paths)
    assert all(path.parent == DEFAULT_ECOMMERCE_DOCS_DIR for path in paths)


def test_load_markdown_documents_is_domain_agnostic(tmp_path: Path) -> None:
    docs_dir = tmp_path / "hr"
    docs_dir.mkdir()
    policy_file = docs_dir / "leave_policy.md"
    policy_file.write_text("# Leave Policy\n\nAnnual leave requires manager approval.", encoding="utf-8")

    documents = load_markdown_documents(docs_dir)

    assert len(documents) == 1
    assert documents[0].source == "leave_policy.md"
    assert documents[0].metadata["document_type"] == "leave_policy"
    assert documents[0].metadata["path"] == "leave_policy.md"


def test_load_markdown_documents_rejects_missing_path(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_markdown_documents(tmp_path / "missing")


def test_ecommerce_mock_data_has_expected_shape() -> None:
    orders = json.loads((PROJECT_ROOT / "data" / "ecommerce" / "mock" / "orders.json").read_text())
    products = json.loads((PROJECT_ROOT / "data" / "ecommerce" / "mock" / "products.json").read_text())

    assert 5 <= len(orders) <= 10
    assert len(products) >= 5

    order_fields = {"order_id", "user_id", "product_id", "status", "created_at", "refund_status"}
    product_ids = {product["product_id"] for product in products}

    for order in orders:
        assert order_fields.issubset(order)
        assert order["product_id"] in product_ids
