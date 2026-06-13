from fastapi.testclient import TestClient

from app.domains.ecommerce.adapter import load_ecommerce_documents
from app.pipeline.chunker import split_documents
from app.pipeline.retriever import KeywordRetriever
from app.pipeline.vector_store import build_index
from app.main import app


client = TestClient(app)


def test_chunks_inherit_document_metadata() -> None:
    documents = load_ecommerce_documents()
    chunks = split_documents(documents, chunk_size=220, overlap=20)

    assert chunks
    for chunk in chunks:
        assert chunk.metadata["source"] == chunk.source
        assert chunk.metadata["document_id"] == chunk.document_id
        assert "chunk_index" in chunk.metadata
        assert "document_type" in chunk.metadata
        assert "policy_version" in chunk.metadata
        assert "applicable_scenario" in chunk.metadata


def test_retriever_filters_return_policy_metadata() -> None:
    retriever = KeywordRetriever.from_documents(load_ecommerce_documents(), chunk_size=220, overlap=20)

    evidence = retriever.retrieve(
        "退货需要满足什么条件？",
        top_k=3,
        metadata_filter={"document_type": "return_policy"},
        allow_filter_fallback=False,
    )

    assert evidence
    assert evidence[0].source == "return_policy.md"
    assert all(item.metadata["document_type"] == "return_policy" for item in evidence)
    assert all(item.source != "warranty_policy.md" for item in evidence)


def test_retriever_filters_warranty_policy_metadata() -> None:
    retriever = KeywordRetriever.from_documents(load_ecommerce_documents(), chunk_size=220, overlap=20)

    evidence = retriever.retrieve(
        "耳机保修多久？",
        top_k=3,
        metadata_filter={"document_type": "warranty_policy"},
        allow_filter_fallback=False,
    )

    assert evidence
    assert evidence[0].source == "warranty_policy.md"
    assert all(item.metadata["document_type"] == "warranty_policy" for item in evidence)
    assert all(item.source != "logistics_policy.md" for item in evidence)


def test_metadata_filter_can_return_empty_without_crashing() -> None:
    retriever = KeywordRetriever.from_documents(load_ecommerce_documents(), chunk_size=220, overlap=20)

    evidence = retriever.retrieve(
        "耳机保修多久？",
        top_k=3,
        metadata_filter={"document_type": "nonexistent_policy"},
        allow_filter_fallback=False,
    )

    assert evidence == []


def test_metadata_filter_can_fallback_to_unfiltered_retrieval() -> None:
    retriever = KeywordRetriever.from_documents(load_ecommerce_documents(), chunk_size=220, overlap=20)

    evidence = retriever.retrieve(
        "耳机保修多久？",
        top_k=3,
        metadata_filter={"document_type": "nonexistent_policy"},
        allow_filter_fallback=True,
    )

    assert evidence
    assert evidence[0].source == "warranty_policy.md"


def test_index_search_accepts_metadata_filter() -> None:
    chunks = split_documents(load_ecommerce_documents(), chunk_size=220, overlap=20)
    index = build_index(chunks)

    results = index.search(
        query="配送范围",
        top_k=3,
        metadata_filter={"document_type": "logistics_policy"},
    )

    assert results
    assert all(result.chunk.metadata["document_type"] == "logistics_policy" for result in results)


def test_chat_warranty_query_uses_warranty_metadata_filter() -> None:
    response = client.post(
        "/chat",
        json={
            "user_id": "demo_user_001",
            "session_id": "week2-day3",
            "query": "耳机保修多久？",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "warranty"
    assert payload["route"] == "document_only"
    assert payload["fallback"] is False
    assert payload["evidence"][0]["source"] == "warranty_policy.md"
    assert payload["evidence"][0]["metadata"]["document_type"] == "warranty_policy"
