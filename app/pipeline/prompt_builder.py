from app.schemas.evidence import Evidence


def build_prompt(query: str, evidence: list[Evidence]) -> str:
    context = _format_evidence(evidence)
    return (
        "You are an enterprise RAG copilot. Answer only from the provided evidence.\n"
        "If the evidence is empty or unrelated, say that the system cannot answer from current evidence.\n\n"
        f"User question:\n{query}\n\n"
        f"Evidence:\n{context}"
    )


def _format_evidence(evidence: list[Evidence]) -> str:
    if not evidence:
        return "(no evidence)"

    lines: list[str] = []
    for index, item in enumerate(evidence, start=1):
        lines.append(
            f"[{index}] source={item.source} score={item.score:.4f}\n{item.content}"
        )
    return "\n\n".join(lines)
