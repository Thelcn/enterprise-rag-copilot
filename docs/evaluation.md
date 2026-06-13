# Evaluation

This document explains the local Week 2 ecommerce RAG evaluation loop.

The evaluation is intentionally small and deterministic. It measures behavior on
the repository's mock ecommerce data and markdown policy documents. It is not a
production benchmark and should not be presented as real-world model quality.

## Case File

Cases live in:

```text
evaluation/ecommerce_cases.json
```

Each case contains:

- `id`: stable case identifier.
- `query`: user query sent to `/chat`.
- `expected_intent`: expected intent label.
- `expected_route`: expected route such as `structured_only`, `document_only`,
  `hybrid`, or `fallback`.
- `required_evidence_keywords`: strings that must appear in serialized
  evidence when evidence is expected.
- `expected_fallback`: whether the response should fallback.
- `expected_fallback_reason`: optional reason code for fallback cases.
- `notes`: short explanation of what the case covers.

The current set has 35 cases:

- structured order/refund/product lookups
- document-only return, warranty, and logistics questions
- hybrid order-plus-policy questions
- failure cases for missing IDs, not-found records, unknown intent, and
  high-risk requests

## Metrics

The local runner computes:

- `intent_accuracy`: actual intent equals expected intent.
- `route_accuracy`: actual route equals expected route.
- `fallback_correctness`: actual fallback flag equals expected fallback flag.
- `fallback_reason_accuracy`: fallback reason matches when the case specifies
  an expected reason.
- `evidence_presence_rate`: non-fallback cases returned at least one evidence
  item.
- `evidence_keyword_hit_rate`: required evidence keywords appeared in serialized
  evidence.
- `error_count`: cases that raised an exception or returned non-200 HTTP.
- `average_total_latency_ms`: average local `trace.total_latency_ms` across
  cases that returned trace data.

## Run Command

```powershell
python -m evaluation.run_eval --cases evaluation/ecommerce_cases.json --out evaluation/eval_report.json --markdown-out evaluation/eval_report.md
```

The generated report files are ignored by Git because they contain local
latency values that change between runs.

## Review Rules

- A failed case should be investigated by `case_id`.
- Do not hide runner errors. The report includes per-case `error` fields.
- Do not claim the metrics represent production quality.
- Treat evidence keyword hits as a basic smoke check, not a full faithfulness
  metric.
- Add new failure cases when a bug is found, then add focused tests if the bug
  belongs in code.

## Current Limitations

- The dataset is small and hand-written.
- The documents and structured data are mock ecommerce assets.
- The answer generator is still deterministic and rule-based, not a real LLM.
- There is no semantic faithfulness scoring yet.
- There is no RAGAS or external evaluation framework integration yet.
