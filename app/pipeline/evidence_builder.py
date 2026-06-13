import json
from collections.abc import Iterable, Mapping
from typing import Protocol
from uuid import NAMESPACE_URL, uuid5

from app.schemas.document import MetadataValue
from app.schemas.evidence import Evidence, EvidenceContent, EvidenceType


class ToolResultLike(Protocol):
    tool_name: str
    success: bool
    data: Mapping[str, MetadataValue]
    evidence: Evidence | None
    error_code: str | None


def build_evidence(
    tool_results: Iterable[ToolResultLike] | None = None,
    retrieved_evidence: Iterable[Evidence] | None = None,
) -> list[Evidence]:
    evidence: list[Evidence] = []

    for result in tool_results or []:
        structured_evidence = _evidence_from_tool_result(result)
        if structured_evidence is not None:
            evidence.append(structured_evidence)

    for item in retrieved_evidence or []:
        evidence.append(_normalize_document_evidence(item))

    return evidence


def _evidence_from_tool_result(result: ToolResultLike) -> Evidence | None:
    if not result.success or not result.data:
        return None

    source = result.evidence.source if result.evidence else result.tool_name
    score = result.evidence.score if result.evidence else 1.0
    metadata = dict(result.evidence.metadata) if result.evidence else {}
    metadata.update(
        {
            "tool_name": result.tool_name,
            "evidence_origin": "structured_tool",
        }
    )
    content = dict(result.data)

    return Evidence(
        evidence_id=build_evidence_id("structured", source, content),
        evidence_type="structured",
        source=source,
        content=content,
        score=score,
        metadata=metadata,
    )


def _normalize_document_evidence(item: Evidence) -> Evidence:
    return Evidence(
        evidence_id=build_evidence_id("document", item.source, item.content),
        evidence_type="document",
        source=item.source,
        content=item.content,
        score=item.score,
        metadata=item.metadata,
    )


def build_evidence_id(
    evidence_type: EvidenceType,
    source: str,
    content: EvidenceContent,
) -> str:
    stable_content = json.dumps(content, ensure_ascii=False, sort_keys=True)
    stable_key = f"{evidence_type}:{source}:{stable_content}"
    return f"ev_{uuid5(NAMESPACE_URL, stable_key).hex}"
