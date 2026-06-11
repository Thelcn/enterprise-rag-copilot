import re
from uuid import NAMESPACE_URL, uuid5

from app.schemas.document import Chunk, Document

# 文档切分器，将文档分割成更小的文本块，便于后续处理和索引
def split_documents(
    documents: list[Document],
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[Chunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")
    if overlap < 0:
        raise ValueError("overlap must be greater than or equal to 0")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    chunks: list[Chunk] = []
    for document in documents:
        document_chunks = _split_single_document(document, chunk_size, overlap)
        chunks.extend(document_chunks)
    return chunks


def _split_single_document(document: Document, chunk_size: int, overlap: int) -> list[Chunk]:
    text_chunks = _split_text(document.content, chunk_size, overlap)
    chunks: list[Chunk] = []

    for index, content in enumerate(text_chunks):
        chunk_metadata = {
            **document.metadata,
            "document_id": document.id,
            "chunk_index": index,
        }
        chunks.append(
            Chunk(
                id=_build_chunk_id(document.id, index, content),
                document_id=document.id,
                source=document.source,
                content=content,
                metadata=chunk_metadata,
            )
        )

    return chunks


def _split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    if not paragraphs:
        return []

    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if len(paragraph) > chunk_size:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_split_long_text(paragraph, chunk_size, overlap))
            continue

        candidate = paragraph if not current else f"{current}\n\n{paragraph}"
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            chunks.append(current)
            current = _overlap_tail(current, overlap, paragraph)

    if current:
        chunks.append(current)

    return chunks


def _split_long_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    chunks: list[str] = []
    start = 0
    step = chunk_size - overlap

    while start < len(text):
        chunk = text[start : start + chunk_size].strip()
        if chunk:
            chunks.append(chunk)
        start += step

    return chunks

# 处理重叠部分
def _overlap_tail(previous: str, overlap: int, next_text: str) -> str:
    if overlap == 0:
        return next_text
    tail = previous[-overlap:].strip()
    return f"{tail}\n\n{next_text}" if tail else next_text

# 构建chunk id，确保同一文档、同一位置的chunk具有相同id，便于去重和更新
def _build_chunk_id(document_id: str, chunk_index: int, content: str) -> str:
    stable_key = f"{document_id}:{chunk_index}:{content}"
    return f"chunk_{uuid5(NAMESPACE_URL, stable_key).hex}"
