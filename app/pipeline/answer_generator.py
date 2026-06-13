import json

from app.schemas.evidence import Evidence


def generate_answer(prompt: str, evidence: list[Evidence]) -> str:
    if not evidence:
        return "I cannot answer from the current evidence."

    selected = evidence[:2]
    evidence_summary = " ".join(_clean_content(item) for item in selected)
    sources = ", ".join(dict.fromkeys(item.source for item in selected))
    return f"根据当前检索到的证据（{sources}）：{evidence_summary}"


def _clean_content(evidence: Evidence) -> str:
    if isinstance(evidence.content, dict):
        return _format_structured_content(evidence.content)

    lines = []
    for line in evidence.content.splitlines():
        cleaned = line.strip("# ").strip()
        if not cleaned or _looks_like_metadata_line(cleaned):
            continue
        lines.append(cleaned)
    return " ".join(lines)


def _format_structured_content(content: dict[str, object]) -> str:
    return json.dumps(content, ensure_ascii=False, sort_keys=True)


def _looks_like_metadata_line(line: str) -> bool:
    metadata_markers = (
        "政策元数据",
        "政策版本",
        "文档类型",
        "适用场景",
        "适用品类",
    )
    return any(marker in line for marker in metadata_markers)
