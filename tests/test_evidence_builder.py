from app.domains.ecommerce.repository import EcommerceRepository
from app.domains.ecommerce.tools import EcommerceTools
from app.pipeline.evidence_builder import build_evidence, build_evidence_id
from app.schemas.evidence import Evidence


def test_build_evidence_converts_tool_result_to_structured_evidence() -> None:
    tools = EcommerceTools(repository=EcommerceRepository())
    tool_result = tools.get_order_status("ORD-1001")

    evidence = build_evidence(tool_results=[tool_result])

    assert len(evidence) == 1
    item = evidence[0]
    assert item.evidence_id.startswith("ev_")
    assert item.evidence_type == "structured"
    assert item.source == "structured:orders:ORD-1001"
    assert isinstance(item.content, dict)
    assert item.content["order_id"] == "ORD-1001"
    assert item.metadata["tool_name"] == "get_order_status"


def test_build_evidence_ignores_failed_tool_result() -> None:
    tools = EcommerceTools(repository=EcommerceRepository())
    tool_result = tools.get_order_status(None)

    evidence = build_evidence(tool_results=[tool_result])

    assert evidence == []


def test_build_evidence_preserves_document_evidence_metadata() -> None:
    retrieved = Evidence(
        source="return_policy.md",
        content="签收后 7 天内可以申请无理由退货。",
        score=0.82,
        metadata={"document_type": "return_policy"},
    )

    evidence = build_evidence(retrieved_evidence=[retrieved])

    assert len(evidence) == 1
    item = evidence[0]
    assert item.evidence_type == "document"
    assert item.source == "return_policy.md"
    assert item.content == "签收后 7 天内可以申请无理由退货。"
    assert item.metadata["document_type"] == "return_policy"


def test_build_evidence_combines_structured_and_document_evidence() -> None:
    tools = EcommerceTools(repository=EcommerceRepository())
    tool_result = tools.get_order_status("ORD-1001")
    retrieved = Evidence(
        source="return_policy.md",
        content="退货需要保持商品和包装完整。",
        score=0.72,
        metadata={"document_type": "return_policy"},
    )

    evidence = build_evidence(tool_results=[tool_result], retrieved_evidence=[retrieved])

    assert [item.evidence_type for item in evidence] == ["structured", "document"]
    assert evidence[0].source == "structured:orders:ORD-1001"
    assert evidence[1].source == "return_policy.md"


def test_build_evidence_id_is_stable() -> None:
    first = build_evidence_id("document", "return_policy.md", "same content")
    second = build_evidence_id("document", "return_policy.md", "same content")

    assert first == second
