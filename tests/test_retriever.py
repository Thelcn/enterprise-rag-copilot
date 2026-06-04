from app.domains.ecommerce.adapter import load_ecommerce_documents
from app.pipeline.chunker import split_documents
from app.pipeline.retriever import KeywordRetriever
from app.pipeline.vector_store import build_index
from app.schemas.document import Document


def test_split_documents_creates_chunks_with_metadata() -> None:
    documents = load_ecommerce_documents()
    chunks = split_documents(documents, chunk_size=220, overlap=20)

    assert len(chunks) >= len(documents)
    assert all(chunk.id.startswith("chunk_") for chunk in chunks)
    assert all(chunk.document_id for chunk in chunks)
    assert all(chunk.content for chunk in chunks)
    assert all("chunk_index" in chunk.metadata for chunk in chunks)


def test_retriever_returns_return_policy_for_return_query() -> None:
    documents = load_ecommerce_documents()
    retriever = KeywordRetriever.from_documents(documents, chunk_size=220, overlap=20)

    evidence = retriever.retrieve("七天无理由退货", top_k=3)

    assert evidence
    assert evidence[0].source == "return_policy.md"
    assert "退货" in evidence[0].content
    assert 0.0 < evidence[0].score <= 1.0


def test_retriever_returns_evidence_not_answer() -> None:
    documents = load_ecommerce_documents()
    retriever = KeywordRetriever.from_documents(documents)

    evidence = retriever.retrieve("保修范围", top_k=2)

    assert evidence
    assert all(hasattr(item, "source") for item in evidence)
    assert all(hasattr(item, "content") for item in evidence)
    assert all(hasattr(item, "score") for item in evidence)
    assert not hasattr(evidence[0], "answer")


def test_retriever_returns_empty_for_blank_query() -> None:
    documents = load_ecommerce_documents()
    retriever = KeywordRetriever.from_documents(documents)

    assert retriever.retrieve("   ") == []


def test_keyword_fallback_is_deterministic() -> None:
    documents = load_ecommerce_documents()
    retriever = KeywordRetriever.from_documents(documents, chunk_size=220, overlap=20)

    first = retriever.retrieve("物流异常", top_k=2)
    second = retriever.retrieve("物流异常", top_k=2)

    assert first == second


def test_index_and_loader_are_domain_agnostic() -> None:
    document = Document(
        id="doc_hr_leave",
        source="leave_policy.md",
        content="Annual leave requires manager approval. Sick leave requires documentation.",
        metadata={"document_type": "leave_policy"},
    )
    chunks = split_documents([document], chunk_size=80, overlap=10)
    index = build_index(chunks)
    retriever = KeywordRetriever(index=index)

    evidence = retriever.retrieve("manager approval", top_k=1)

    assert evidence
    assert evidence[0].source == "leave_policy.md"
