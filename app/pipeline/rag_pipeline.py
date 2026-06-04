from app.pipeline.answer_generator import generate_answer
from app.pipeline.prompt_builder import build_prompt
from app.pipeline.retriever import KeywordRetriever
from app.schemas.chat import ChatResponse
from app.schemas.document import Document
from app.schemas.evidence import Evidence
from app.schemas.trace import new_trace_id


MIN_RETRIEVAL_SCORE = 0.05


class RagPipeline:
    def __init__(self, retriever: KeywordRetriever, min_score: float = MIN_RETRIEVAL_SCORE) -> None:
        self.retriever = retriever
        self.min_score = min_score

    @classmethod
    def from_documents(
        cls,
        documents: list[Document],
        chunk_size: int = 500,
        overlap: int = 50,
        min_score: float = MIN_RETRIEVAL_SCORE,
    ) -> "RagPipeline":
        retriever = KeywordRetriever.from_documents(
            documents,
            chunk_size=chunk_size,
            overlap=overlap,
        )
        return cls(retriever=retriever, min_score=min_score)

    def run_chat(self, query: str, user_id: str, session_id: str, top_k: int = 3) -> ChatResponse:
        trace_id = new_trace_id()
        evidence = self.retriever.retrieve(query, top_k=top_k)
        evidence = _filter_evidence_by_score(evidence, min_score=self.min_score)

        if not evidence:
            return ChatResponse(
                answer="我没有在当前知识库中找到足够可靠的证据来回答这个问题。",
                intent="unknown",
                evidence=[],
                fallback=True,
                fallback_reason="No retrieval evidence met the minimum score threshold.",
                trace_id=trace_id,
            )

        prompt = build_prompt(query=query, evidence=evidence)
        answer = generate_answer(prompt=prompt, evidence=evidence)
        return ChatResponse(
            answer=answer,
            intent="policy_question",
            evidence=evidence,
            fallback=False,
            fallback_reason=None,
            trace_id=trace_id,
        )


def run_chat(
    query: str,
    user_id: str,
    session_id: str,
    documents: list[Document],
    top_k: int = 3,
) -> ChatResponse:
    pipeline = RagPipeline.from_documents(documents)
    return pipeline.run_chat(query=query, user_id=user_id, session_id=session_id, top_k=top_k)


def _filter_evidence_by_score(evidence: list[Evidence], min_score: float) -> list[Evidence]:
    return [item for item in evidence if item.score >= min_score]
