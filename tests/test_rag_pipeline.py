from fastapi.testclient import TestClient

from app.domains.ecommerce.adapter import load_ecommerce_documents
from app.main import app
from app.pipeline.answer_generator import generate_answer
from app.pipeline.prompt_builder import build_prompt
from app.pipeline.rag_pipeline import RagPipeline


client = TestClient(app)


def test_rag_pipeline_returns_evidence_grounded_policy_answer() -> None:
    pipeline = RagPipeline.from_documents(load_ecommerce_documents(), chunk_size=220, overlap=20)

    response = pipeline.run_chat(
        query="耳机可以退货吗？",
        user_id="u1",
        session_id="s1",
    )

    assert response.fallback is False
    assert response.fallback_reason is None
    assert response.intent == "policy_question"
    assert response.route == "document_only"
    assert response.evidence
    assert response.evidence[0].source == "return_policy.md"
    assert "退货" in response.answer
    assert response.trace_id.startswith("trace_")


def test_rag_pipeline_fallbacks_when_no_evidence_matches() -> None:
    pipeline = RagPipeline.from_documents(load_ecommerce_documents(), chunk_size=220, overlap=20)

    response = pipeline.run_chat(
        query="量子咖啡会员积分怎么兑换？",
        user_id="u1",
        session_id="s1",
    )

    assert response.fallback is True
    assert response.fallback_reason == "No retrieval evidence met the minimum score threshold."
    assert response.evidence == []
    assert "没有在当前知识库中找到" in response.answer


def test_prompt_builder_includes_query_and_evidence() -> None:
    pipeline = RagPipeline.from_documents(load_ecommerce_documents(), chunk_size=220, overlap=20)
    evidence = pipeline.retriever.retrieve("保修范围", top_k=1)

    prompt = build_prompt(query="保修范围是什么？", evidence=evidence)

    assert "保修范围是什么？" in prompt
    assert evidence[0].source in prompt
    assert evidence[0].content in prompt


def test_answer_generator_does_not_answer_without_evidence() -> None:
    prompt = build_prompt(query="未知问题", evidence=[])

    answer = generate_answer(prompt=prompt, evidence=[])

    assert answer == "I cannot answer from the current evidence."


def test_chat_endpoint_uses_rag_pipeline() -> None:
    response = client.post(
        "/chat",
        json={
            "user_id": "u1",
            "session_id": "s1",
            "query": "退货政策是什么？",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["fallback"] is False
    assert payload["route"] == "document_only"
    assert payload["evidence"]
    assert payload["evidence"][0]["source"] == "return_policy.md"
    assert payload["trace_id"].startswith("trace_")
