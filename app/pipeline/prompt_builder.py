import json

from app.schemas.evidence import Evidence


def build_prompt(query: str, evidence: list[Evidence]) -> str:
    context = _format_evidence(evidence)
    return (
        "You are an enterprise RAG copilot.\n"
        "Answer only from the Evidence items below.\n"
        "Do not introduce order, refund, product, policy, or timeline facts that are absent from Evidence.\n"
        "If Evidence is empty or insufficient, say that the system cannot answer from current evidence.\n"
        "When possible, mention the source names that support the answer.\n\n"
        f"User question:\n{query}\n\n"
        f"Evidence:\n{context}"
    )


def _format_evidence(evidence: list[Evidence]) -> str:
    if not evidence:
        return "(no evidence)"

    lines: list[str] = []
    for index, item in enumerate(evidence, start=1):
        score = "n/a" if item.score is None else f"{item.score:.4f}"
        lines.append(
            f"[{index}] id={item.evidence_id} type={item.evidence_type} source={item.source} score={score}\n"
            f"metadata={json.dumps(item.metadata, ensure_ascii=False, sort_keys=True)}\n"
            f"content={_format_content(item)}"
        )
    return "\n\n".join(lines)


def _format_content(item: Evidence) -> str:
    if isinstance(item.content, dict):
        return json.dumps(item.content, ensure_ascii=False, sort_keys=True)
    return item.content
