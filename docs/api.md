# API Contract

This document records the current API contract and the Week 2 target shape.
The implementation must remain stable while the hybrid RAG upgrade is added in
small steps.

## `GET /health`

Returns service metadata and is used by smoke tests, Docker checks, and local
development.

Current response:

```json
{
  "status": "ok",
  "service": "enterprise-rag-copilot",
  "version": "0.1.0",
  "environment": "development"
}
```

Field meanings:

- `status`: health status for the service process.
- `service`: configured service name.
- `version`: configured service version.
- `environment`: configured runtime environment.

## `POST /chat`

Runs the RAG chat flow.

### Current Request

```json
{
  "user_id": "u1",
  "session_id": "s1",
  "query": "退货政策是什么？"
}
```

Field meanings:

- `user_id`: caller identifier. It is required and trimmed before validation.
- `session_id`: conversation/session identifier. It is required and trimmed
  before validation.
- `query`: user question. It is required, trimmed, and must contain at least two
  non-whitespace characters.

### Current Response

```json
{
  "answer": "根据当前检索到的证据（return_policy.md）：...",
  "intent": "policy_question",
  "route": "document_only",
  "evidence": [
    {
      "evidence_id": "ev_...",
      "evidence_type": "document",
      "source": "return_policy.md",
      "content": "签收后 7 天内，未拆封或不影响二次销售的商品可申请无理由退货。",
      "score": 0.2459,
      "metadata": {
        "document_type": "return_policy",
        "policy_version": "ecommerce-policy-2026-06",
        "applicable_scenario": "return_request"
      }
    }
  ],
  "fallback": false,
  "fallback_reason": null,
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

Current field meanings:

- `answer`: final answer generated from retrieved evidence. In Week 1 this is a
  deterministic rule-based answer, not a real LLM answer.
- `intent`: intent label returned by the intent router or current RAG pipeline.
- `route`: route selected for the request. Current values include
  `structured_only`, `document_only`, `hybrid`, and `fallback`.
- `evidence`: structured or document evidence used to support the answer.
- `evidence[].evidence_id`: stable evidence identifier generated from evidence
  type, source, and content.
- `evidence[].evidence_type`: `document` for retrieved policy chunks or
  `structured` for tool/repository facts.
- `evidence[].source`: source document name.
- `evidence[].content`: retrieved chunk text for document evidence, or a
  structured object for tool evidence.
- `evidence[].score`: retriever score for the evidence item.
- `evidence[].metadata`: document or tool metadata. Week 2 Day 3 adds
  `document_type`, `product_category`, `policy_version`, and
  `applicable_scenario` for ecommerce policy documents.
- `fallback`: whether the system refused to answer from insufficient evidence.
- `fallback_reason`: stable fallback reason code, or `null` when the answer is
  supported.
- `trace_id`: request trace identifier for logs and debugging.
- `trace`: local performance trace with stage timings. It is for development
  and evaluation, not a production performance claim.

### Current Fallback Response

```json
{
  "answer": "我没有识别出这个问题需要查询哪类企业知识或业务数据。",
  "intent": "unknown",
  "route": "fallback",
  "evidence": [],
  "fallback": true,
  "fallback_reason": "unknown_intent",
  "trace_id": "trace_...",
  "trace": {
    "trace_id": "trace_...",
    "total_latency_ms": 0.12,
    "stages": [
      {
        "name": "intent",
        "latency_ms": 0.03,
        "metadata": {}
      },
      {
        "name": "fallback",
        "latency_ms": 0.01,
        "metadata": {
          "reason": "unknown_intent"
        }
      }
    ]
  }
}
```

Fallback means the service could not produce a safe, grounded answer because
intent, required business data, policy evidence, or safety constraints were not
satisfied. It should not invent missing facts.

### Current Structured Response

Week 2 Day 2 adds structured ecommerce tools. Order, refund, and product fact
questions can return structured evidence instead of document evidence.

Example request:

```json
{
  "user_id": "demo_user_001",
  "session_id": "week2_demo_session",
  "query": "我的订单 ORD-1001 现在是什么状态？"
}
```

Example response shape:

```json
{
  "answer": "订单 ORD-1001 当前状态是 已签收，关联商品是 P-HEADPHONE-01，退款状态是 未申请。",
  "intent": "order_status",
  "route": "structured_only",
  "evidence": [
    {
      "evidence_id": "ev_...",
      "evidence_type": "structured",
      "source": "structured:orders:ORD-1001",
      "content": {
        "order_id": "ORD-1001",
        "status": "delivered",
        "status_label": "已签收"
      },
      "score": 1.0,
      "metadata": {
        "tool_name": "get_order_status",
        "evidence_origin": "structured_tool"
      }
    }
  ],
  "fallback": false,
  "fallback_reason": null,
  "trace_id": "trace_...",
  "trace": {
    "trace_id": "trace_...",
    "total_latency_ms": 0.2,
    "stages": [
      {
        "name": "intent",
        "latency_ms": 0.03,
        "metadata": {}
      },
      {
        "name": "tool",
        "latency_ms": 0.05,
        "metadata": {
          "intent": "order_status",
          "tool_name": "get_order_status"
        }
      }
    ]
  }
}
```

## Week 2 Target Response

Week 2 will continue extending the response shape as tracing features are
introduced. The target shape is:

```json
{
  "answer": "string",
  "intent": "return_policy",
  "route": "document_only",
  "evidence": [
    {
      "evidence_id": "ev_...",
      "evidence_type": "document",
      "source": "return_policy.md",
      "content": "string or object",
      "score": 0.82,
      "metadata": {
        "domain": "ecommerce",
        "policy_type": "return"
      }
    }
  ],
  "fallback": false,
  "fallback_reason": null,
  "trace_id": "trace_...",
  "trace": {
    "trace_id": "trace_...",
    "total_latency_ms": 1.23,
    "stages": []
  }
}
```

Target field meanings:

- `route`: routing decision from the intent router.
- `evidence[].evidence_id`: stable identifier for an evidence item inside one
  response. Day 4 generates this through the evidence builder.
- `evidence[].evidence_type`: `structured` for tool/repository facts or
  `document` for retrieved knowledge-base chunks.
- `evidence[].content`: text for document evidence or a structured object for
  tool evidence.
- `evidence[].metadata`: optional attributes for filtering, display, evaluation,
  and debugging.
- `trace`: optional debug/local trace payload. It may include stage timings such
  as intent routing, tool lookup, retrieval, answer generation, and total
  latency. Any performance values must come from measured local traces.

## Week 2 Fallback Semantics

Week 2 fallback should cover more than low document-retrieval confidence:

- unknown intent
- missing required slots, such as an absent order ID
- structured tool record not found
- weak or empty document evidence
- hybrid question where either structured evidence or document evidence is
  missing
- unsupported or high-risk question that cannot be grounded in evidence

Current fallback reason examples include `unknown_intent`, `missing_order_id`,
`order_not_found`, `missing_refund_id`, `refund_not_found`,
`missing_product_id`, `product_not_found`, `no_evidence`,
`low_retrieval_score`, `hybrid_document_evidence_missing`,
`hybrid_structured_evidence_missing`, and `high_risk_request`.

The answer should remain conservative when `fallback=true`.

## Local Smoke Commands

```powershell
curl.exe -s http://127.0.0.1:8000/health
curl.exe -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"user_id":"u1","session_id":"s1","query":"退货政策是什么？"}'
```
