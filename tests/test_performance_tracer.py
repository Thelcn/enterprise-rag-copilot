from app.domains.ecommerce.adapter import load_ecommerce_documents
from app.pipeline.performance_tracer import PerformanceTracer
from app.pipeline.rag_pipeline import RagPipeline


def test_performance_tracer_records_stage_latency() -> None:
    tracer = PerformanceTracer(trace_id="trace_test")

    with tracer.span("intent", route="document_only"):
        pass

    trace = tracer.finish()

    assert trace.trace_id == "trace_test"
    assert trace.total_latency_ms is not None
    assert trace.total_latency_ms >= 0
    assert len(trace.stages) == 1
    assert trace.stages[0].name == "intent"
    assert trace.stages[0].latency_ms >= 0
    assert trace.stages[0].metadata["route"] == "document_only"


def test_rag_pipeline_returns_trace_stages() -> None:
    pipeline = RagPipeline.from_documents(load_ecommerce_documents(), chunk_size=220, overlap=20)

    response = pipeline.run_chat(
        query="退货政策是什么？",
        user_id="u1",
        session_id="s1",
    )

    assert response.trace is not None
    assert response.trace.trace_id == response.trace_id
    assert response.trace.total_latency_ms is not None
    stage_names = [stage.name for stage in response.trace.stages]
    assert "retrieval" in stage_names
    assert "rerank_mock" in stage_names
    assert "llm_mock" in stage_names
