# Query API Contract

This document defines the current `/chat` API contract for Enterprise RAG
Copilot. Week 1 connected the endpoint to a naive RAG v0 pipeline, and Week 2
adds route information for hybrid RAG.

## `GET /health`

Returns service metadata.

Example response:

```json
{
  "status": "ok",
  "service": "enterprise-rag-copilot",
  "version": "0.1.0",
  "environment": "development"
}
```

## `POST /chat`

Accepts one user question in a session and returns a structured answer object.

### Request

```json
{
  "user_id": "demo_user_001",
  "session_id": "week1_demo_session",
  "query": "我买的耳机可以七天无理由退货吗？"
}
```

### Request Fields

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `user_id` | string | yes | Non-empty user identifier. Whitespace is stripped. |
| `session_id` | string | yes | Non-empty conversation/session identifier. Whitespace is stripped. |
| `query` | string | yes | User question. Whitespace is stripped. Must contain at least 2 characters and at most 1000 characters. |

### Successful Response Example

```json
{
  "answer": "根据当前检索到的证据（return_policy.md）：退货政策 七天无理由退货 签收后 7 天内...",
  "intent": "policy_question",
  "route": "document_only",
  "evidence": [
    {
      "evidence_id": "ev_...",
      "evidence_type": "document",
      "source": "return_policy.md",
      "content": "签收后 7 天内，未拆封或不影响二次销售的商品可申请无理由退货。",
      "score": 0.4812,
      "metadata": {
        "document_type": "return_policy",
        "policy_version": "ecommerce-policy-2026-06",
        "applicable_scenario": "return_request"
      }
    }
  ],
  "fallback": false,
  "fallback_reason": null,
  "trace_id": "trace_2ad8e0b78b5741a4a53a87b2d98ff3e6",
  "trace": {
    "trace_id": "trace_2ad8e0b78b5741a4a53a87b2d98ff3e6",
    "total_latency_ms": 1.23,
    "stages": []
  }
}
```

### Fallback Response Example

Request:

```json
{
  "user_id": "u1",
  "session_id": "s1",
  "query": "量子咖啡会员积分怎么兑换？"
}
```

Response:

```json
{
  "answer": "我没有识别出这个问题需要查询哪类企业知识或业务数据。",
  "intent": "unknown",
  "route": "fallback",
  "evidence": [],
  "fallback": true,
  "fallback_reason": "unknown_intent",
  "trace_id": "trace_0eb3763a9cb54b74a3b52ae21fc844a3",
  "trace": {
    "trace_id": "trace_0eb3763a9cb54b74a3b52ae21fc844a3",
    "total_latency_ms": 0.12,
    "stages": []
  }
}
```

### Response Fields

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `answer` | string | yes | Final answer text. In RAG v0 it is generated only from retrieved evidence. |
| `intent` | string | yes | Query intent label. Week 1 uses simple labels such as `policy_question` and `unknown`. |
| `route` | string | yes | Week 2 routing decision such as `structured_only`, `document_only`, `hybrid`, or `fallback`. |
| `evidence` | array | yes | List of evidence objects returned by retrieval. |
| `fallback` | boolean | yes | Whether the system used a fallback path. |
| `fallback_reason` | string or null | yes | Stable reason code when `fallback` is true. |
| `trace_id` | string | yes | Request trace identifier. Week 1 generates a UUID-based value with a `trace_` prefix. |
| `trace` | object or null | yes | Local trace summary with `total_latency_ms` and stage timings. |

### Evidence Object

```json
{
  "evidence_id": "ev_...",
  "evidence_type": "document",
  "source": "return_policy.md",
  "content": "签收后 7 天内，未拆封或不影响二次销售的商品可申请无理由退货。",
  "score": 0.82,
  "metadata": {
    "document_type": "return_policy",
    "product_category": "all",
    "policy_version": "ecommerce-policy-2026-06",
    "applicable_scenario": "return_request"
  }
}
```

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `evidence_id` | string | yes | Stable evidence identifier generated from type, source, and content. |
| `evidence_type` | string | yes | `document` for retrieved policy chunks, `structured` for tool/repository facts. |
| `source` | string | yes | Source document name or source identifier. |
| `content` | string or object | yes | Evidence text returned by retrieval, or structured fields returned by a tool. |
| `score` | number | yes | Relevance score between `0.0` and `1.0`. Week 1 score semantics may be simple, but must stay explicit. |
| `metadata` | object | yes | Source metadata. Week 2 policy evidence includes `document_type`, `product_category`, `policy_version`, and `applicable_scenario`. |

## Validation Behavior

Invalid requests return FastAPI/Pydantic `422 Unprocessable Entity` responses.

Examples of invalid input:

```json
{
  "user_id": "u1",
  "session_id": "s1",
  "query": ""
}
```

```json
{
  "user_id": "u1",
  "session_id": "s1",
  "query": "a"
}
```

## Current Boundary

Day 6 runs a hybrid RAG prototype with local evaluation and tracing:

```text
query -> route -> optional structured tool -> retrieve -> evidence -> fallback/answer -> trace -> ChatResponse
```

The retriever uses a deterministic keyword fallback, not a semantic embedding
model. The answer generator is rule-based and only organizes retrieved evidence.
If the system cannot produce a safe, grounded answer because intent, required
business data, policy evidence, or safety constraints are not satisfied, `/chat`
returns `fallback=true`.

Current fallback reason examples include `unknown_intent`, `missing_order_id`,
`order_not_found`, `missing_refund_id`, `refund_not_found`,
`missing_product_id`, `product_not_found`, `no_evidence`,
`low_retrieval_score`, `hybrid_document_evidence_missing`,
`hybrid_structured_evidence_missing`, and `high_risk_request`.

Evaluation assets live in `evaluation/`, and local trace metrics are documented
in `docs/performance.md`.

## Week 1 Verification

Verified on 2026-06-04:

```powershell
python -m pytest -q
```

Result:

```text
21 passed
```

Manual `/chat` checks covered one successful policy query and one fallback query.
