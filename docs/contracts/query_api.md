# Query API Contract

This document defines the Week 1 `/chat` API contract for Enterprise RAG
Copilot. Day 2 keeps the endpoint in mock mode, but the request and response
shape is intentionally stable so retrieval, evidence, fallback, and tracing can
be added later without breaking clients.

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

### Day 2 Mock Response

```json
{
  "answer": "This is a Day 2 mock response. The /chat API contract is ready, but retrieval and evidence-grounded generation are not connected yet.",
  "intent": "mock_intent",
  "evidence": [],
  "fallback": true,
  "fallback_reason": "Day 2 mock mode: retrieval is not connected yet.",
  "trace_id": "trace_2ad8e0b78b5741a4a53a87b2d98ff3e6"
}
```

### Response Fields

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `answer` | string | yes | Final answer text. In Day 2 this is a mock response. From Day 5 onward it must be grounded in retrieved evidence. |
| `intent` | string | yes | Query intent label. In Day 2 this is `mock_intent`; later versions can replace it with heuristic or routed intent. |
| `evidence` | array | yes | List of evidence objects. Day 2 returns an empty list because retrieval is not connected yet. |
| `fallback` | boolean | yes | Whether the system used a fallback path. Day 2 returns `true` to avoid pretending mock output is retrieval-backed. |
| `fallback_reason` | string or null | yes | Human-readable reason when `fallback` is true. |
| `trace_id` | string | yes | Request trace identifier. Day 2 generates a UUID-based value with a `trace_` prefix. |

### Evidence Object

```json
{
  "source": "return_policy.md",
  "content": "签收后 7 天内，未拆封或不影响二次销售的商品可申请无理由退货。",
  "score": 0.82
}
```

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `source` | string | yes | Source document name or source identifier. |
| `content` | string | yes | Evidence text returned by retrieval. |
| `score` | number | yes | Relevance score between `0.0` and `1.0`. Week 1 score semantics may be simple, but must stay explicit. |

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

Day 2 only fixes the API contract. It does not run retrieval, build prompts, or
generate evidence-grounded answers. Those behaviors will be added later through
the generic RAG pipeline while preserving this response shape.
