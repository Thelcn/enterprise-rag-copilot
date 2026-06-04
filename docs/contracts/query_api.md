# Query API Contract

This document defines the Week 1 `/chat` API contract for Enterprise RAG
Copilot. Day 5 connects the endpoint to a naive RAG v0 pipeline while preserving
the Day 2 response shape.

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
  "evidence": [
    {
      "source": "return_policy.md",
      "content": "签收后 7 天内，未拆封或不影响二次销售的商品可申请无理由退货。",
      "score": 0.4812
    }
  ],
  "fallback": false,
  "fallback_reason": null,
  "trace_id": "trace_2ad8e0b78b5741a4a53a87b2d98ff3e6"
}
```

### Response Fields

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `answer` | string | yes | Final answer text. In RAG v0 it is generated only from retrieved evidence. |
| `intent` | string | yes | Query intent label. Week 1 uses simple labels such as `policy_question` and `unknown`. |
| `evidence` | array | yes | List of evidence objects returned by retrieval. |
| `fallback` | boolean | yes | Whether the system used a fallback path. |
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

Day 5 runs a naive RAG v0 pipeline:

```text
query -> retrieve -> build_prompt -> generate_answer -> ChatResponse
```

The retriever uses a deterministic keyword fallback, not a semantic embedding
model. The answer generator is rule-based and only organizes retrieved evidence.
If retrieval returns no sufficiently relevant evidence, `/chat` returns
`fallback=true`.
