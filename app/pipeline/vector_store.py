from dataclasses import dataclass
from collections.abc import Mapping

from app.pipeline.embedder import KeywordEmbedder, KeywordVector, cosine_similarity
from app.schemas.document import Chunk, MetadataValue


@dataclass(frozen=True)
class SearchResult:
    chunk: Chunk
    score: float


class InMemoryIndex:
    """Small keyword fallback index for Week 1 local retrieval tests."""

    def __init__(self, embedder: KeywordEmbedder | None = None) -> None:
        self.embedder = embedder or KeywordEmbedder()
        self._chunks: list[Chunk] = []
        self._vectors: list[KeywordVector] = []

    @property
    def chunks(self) -> list[Chunk]:
        return list(self._chunks)

    def add_chunks(self, chunks: list[Chunk]) -> None:
        for chunk in chunks:
            self._chunks.append(chunk)
            self._vectors.append(self.embedder.embed(chunk.content))

    def search(
        self,
        query: str,
        top_k: int = 3,
        metadata_filter: Mapping[str, object] | None = None,
    ) -> list[SearchResult]:
        if top_k <= 0:
            raise ValueError("top_k must be greater than 0")

        query_vector = self.embedder.embed(query)
        if not query_vector:
            return []

        results: list[SearchResult] = []
        for chunk, vector in zip(self._chunks, self._vectors):
            if metadata_filter and not _metadata_matches(chunk.metadata, metadata_filter):
                continue
            score = cosine_similarity(query_vector, vector)
            if score > 0:
                results.append(SearchResult(chunk=chunk, score=round(score, 4)))

        return sorted(
            results,
            key=lambda result: (-result.score, result.chunk.source, result.chunk.id),
        )[:top_k]


def build_index(chunks: list[Chunk], embedder: KeywordEmbedder | None = None) -> InMemoryIndex:
    index = InMemoryIndex(embedder=embedder)
    index.add_chunks(chunks)
    return index


def _metadata_matches(
    metadata: Mapping[str, MetadataValue],
    metadata_filter: Mapping[str, object],
) -> bool:
    for key, expected in metadata_filter.items():
        if key not in metadata:
            return False
        actual = metadata[key]
        if isinstance(expected, (list, tuple, set)):
            if isinstance(actual, list):
                if not set(actual).intersection(set(expected)):
                    return False
            elif actual not in expected:
                return False
        elif isinstance(actual, list):
            if expected not in actual:
                return False
        elif actual != expected:
            return False
    return True
