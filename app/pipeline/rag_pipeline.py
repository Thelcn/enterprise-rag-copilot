from collections.abc import Mapping

from app.core.logging_config import get_logger
from app.pipeline.answer_generator import generate_answer
from app.pipeline.evidence_builder import build_evidence
from app.pipeline.fallback_handler import build_fallback_chat_response, should_fallback
from app.pipeline.performance_tracer import PerformanceTracer
from app.pipeline.prompt_builder import build_prompt
from app.pipeline.retriever import KeywordRetriever
from app.schemas.chat import ChatResponse
from app.schemas.document import Document
from app.schemas.evidence import Evidence


MIN_RETRIEVAL_SCORE = 0.05
logger = get_logger(__name__)


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

    def run_chat(
        self,
        query: str,
        user_id: str,
        session_id: str,
        top_k: int = 3,
        intent: str | None = None,
        route: str = "document_only",
        metadata_filter: Mapping[str, object] | None = None,
        tracer: PerformanceTracer | None = None,
    ) -> ChatResponse:
        owns_tracer = tracer is None
        tracer = tracer or PerformanceTracer()
        trace_id = tracer.trace_id
        response_intent = intent or "policy_question"
        logger.info("rag_stage trace_id=%s stage=start top_k=%s", trace_id, top_k)

        with tracer.span(
            "retrieval",
            top_k=top_k,
            metadata_filter_applied=metadata_filter is not None,
        ):
            retrieval_candidates = self.retriever.retrieve(
                query,
                top_k=top_k,
                metadata_filter=metadata_filter,
            )
            filtered_evidence = _filter_evidence_by_score(retrieval_candidates, min_score=self.min_score)
            evidence = build_evidence(retrieved_evidence=filtered_evidence)
        retrieval_ms = tracer.to_trace_info().stages[-1].latency_ms
        logger.info(
            "rag_stage trace_id=%s stage=retrieve evidence_count=%s latency_ms=%.2f",
            trace_id,
            len(evidence),
            retrieval_ms,
        )

        with tracer.span("rerank_mock", candidate_count=len(retrieval_candidates)):
            reranked_evidence = evidence
        evidence = reranked_evidence

        fallback_route = "document_only" if route == "hybrid" else route
        fallback_decision = should_fallback(
            query=query,
            intent=response_intent,
            route=fallback_route,
            evidence=evidence,
            retrieval_candidates=retrieval_candidates,
            min_score=self.min_score,
        )
        if fallback_decision.fallback:
            with tracer.span("fallback", reason=fallback_decision.reason):
                pass
            trace = tracer.finish() if owns_tracer else tracer.to_trace_info()
            logger.info(
                "rag_stage trace_id=%s stage=fallback reason=%s latency_ms=%.2f",
                trace_id,
                fallback_decision.reason,
                trace.total_latency_ms or 0.0,
            )
            return build_fallback_chat_response(
                decision=fallback_decision,
                intent=response_intent,
                trace_id=trace_id,
                evidence=[],
                trace=trace,
            )

        with tracer.span("llm_mock", evidence_count=len(evidence)):
            prompt = build_prompt(query=query, evidence=evidence)
            answer = generate_answer(prompt=prompt, evidence=evidence)
        trace = tracer.finish() if owns_tracer else tracer.to_trace_info()
        logger.info(
            "rag_stage trace_id=%s stage=answer evidence_count=%s latency_ms=%.2f",
            trace_id,
            len(evidence),
            trace.total_latency_ms or 0.0,
        )
        return ChatResponse(
            answer=answer,
            intent=response_intent,
            route=route,
            evidence=evidence,
            fallback=False,
            fallback_reason=None,
            trace_id=trace_id,
            trace=trace,
        )


def run_chat(
    query: str,
    user_id: str,
    session_id: str,
    documents: list[Document],
    top_k: int = 3,
    intent: str | None = None,
    route: str = "document_only",
    metadata_filter: Mapping[str, object] | None = None,
    tracer: PerformanceTracer | None = None,
) -> ChatResponse:
    pipeline = RagPipeline.from_documents(documents)
    return pipeline.run_chat(
        query=query,
        user_id=user_id,
        session_id=session_id,
        top_k=top_k,
        intent=intent,
        route=route,
        metadata_filter=metadata_filter,
        tracer=tracer,
    )


def _filter_evidence_by_score(evidence: list[Evidence], min_score: float) -> list[Evidence]:
    return [item for item in evidence if item.score >= min_score]
