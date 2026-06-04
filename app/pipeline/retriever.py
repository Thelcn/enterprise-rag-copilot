from app.pipeline.chunker import split_documents
from app.pipeline.embedder import KeywordEmbedder
from app.pipeline.vector_store import InMemoryIndex, build_index
from app.schemas.document import Chunk, Document
from app.schemas.evidence import Evidence


class KeywordRetriever:
    def __init__(self, index: InMemoryIndex) -> None:
        self.index = index

    @classmethod
    def from_documents(
        cls,
        documents: list[Document],
        chunk_size: int = 500,
        overlap: int = 50,
        embedder: KeywordEmbedder | None = None,
    ) -> "KeywordRetriever":
        chunks = split_documents(documents, chunk_size=chunk_size, overlap=overlap)
        return cls(index=build_index(chunks, embedder=embedder))

    @classmethod
    def from_chunks(
        cls,
        chunks: list[Chunk],
        embedder: KeywordEmbedder | None = None,
    ) -> "KeywordRetriever":
        return cls(index=build_index(chunks, embedder=embedder))

    def retrieve(self, query: str, top_k: int = 3) -> list[Evidence]:
        return retrieve(query=query, index=self.index, top_k=top_k)


def retrieve(query: str, index: InMemoryIndex, top_k: int = 3) -> list[Evidence]:
    if not query.strip():
        return []

    results = index.search(query=query, top_k=top_k)
    return [
        Evidence(
            source=result.chunk.source,
            content=result.chunk.content,
            score=result.score,
        )
        for result in results
    ]
