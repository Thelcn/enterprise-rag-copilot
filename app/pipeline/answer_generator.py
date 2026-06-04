from app.schemas.evidence import Evidence


def generate_answer(prompt: str, evidence: list[Evidence]) -> str:
    if not evidence:
        return "I cannot answer from the current evidence."

    selected = evidence[:2]
    evidence_summary = " ".join(_clean_content(item.content) for item in selected)
    sources = ", ".join(dict.fromkeys(item.source for item in selected))
    return f"根据当前检索到的证据（{sources}）：{evidence_summary}"


def _clean_content(content: str) -> str:
    return " ".join(line.strip("# ").strip() for line in content.splitlines() if line.strip())
