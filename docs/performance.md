# Performance Tracing

Week 2 adds local performance tracing so latency numbers come from measured
code paths instead of guesses.

This document defines the tracing contract and how to collect local numbers.
Day 7 can add load-test results, but those results must come from scripts or
trace reports.

## Trace Shape

`POST /chat` responses include:

```json
{
  "trace_id": "trace_...",
  "trace": {
    "trace_id": "trace_...",
    "total_latency_ms": 1.23,
    "stages": [
      {
        "name": "intent",
        "latency_ms": 0.04,
        "metadata": {}
      }
    ]
  }
}
```

`trace_id` remains the stable request identifier. `trace` is the local debug
summary used for evaluation and development.

## Stage Names

Current stage names include:

- `intent`: rule-based intent routing.
- `tool`: structured ecommerce tool lookup.
- `retrieval`: keyword retrieval with optional metadata filter.
- `rerank_mock`: explicit no-op rerank placeholder.
- `llm_mock`: deterministic answer generation placeholder.
- `fallback`: fallback response creation when the system cannot answer safely.

There is no real reranker or LLM yet. The mock stages are present so the later
real components can replace them without changing the trace contract.

## Local Collection

Run the evaluation runner:

```powershell
python -m evaluation.run_eval --cases evaluation/ecommerce_cases.json --out evaluation/eval_report.json --markdown-out evaluation/eval_report.md
```

The JSON report includes per-case `trace_id` and `total_latency_ms`, plus
`average_total_latency_ms` in the metrics summary.

## Rules

- Do not write P95, P99, QPS, or cache hit-rate numbers unless they come from a
  script output or trace report.
- Do not compare local mock latency to production latency.
- Do not log full prompts or full private business records as trace metadata.
- Keep tracing helper logic in `app/pipeline/performance_tracer.py` so business
  code does not become a tangle of ad hoc timers.

## Current Limitations

- Latency is measured in a local Python process.
- The API runner uses FastAPI `TestClient`, not a real network deployment.
- The answer generator is mock/rule-based, so `llm_mock` is not representative
  of hosted LLM latency.
- Day 7 will add local load-test scripts and performance report outputs.
