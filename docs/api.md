# API Contract

This document records the current Week 1 API contract and the Week 2 target
shape. The current implementation must remain stable while the hybrid RAG
upgrade is added in small steps.

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
  "evidence": [
    {
      "source": "return_policy.md",
      "content": "签收后 7 天内，未拆封或不影响二次销售的商品可申请无理由退货。",
      "score": 0.2459
    }
  ],
  "fallback": false,
  "fallback_reason": null,
  "trace_id": "trace_..."
}
```

Current field meanings:

- `answer`: final answer generated from retrieved evidence. In Week 1 this is a
  deterministic rule-based answer, not a real LLM answer.
- `intent`: coarse intent label returned by the current RAG pipeline.
- `evidence`: document evidence used to support the answer.
- `evidence[].source`: source document name.
- `evidence[].content`: retrieved chunk text.
- `evidence[].score`: retriever score for the evidence item.
- `fallback`: whether the system refused to answer from insufficient evidence.
- `fallback_reason`: explanation for fallback, or `null` when the answer is
  supported.
- `trace_id`: request trace identifier for logs and debugging.

### Current Fallback Response

```json
{
  "answer": "我没有在当前知识库中找到足够可靠的证据来回答这个问题。",
  "intent": "unknown",
  "evidence": [],
  "fallback": true,
  "fallback_reason": "No retrieval evidence met the minimum score threshold.",
  "trace_id": "trace_..."
}
```

Fallback means the service did not find enough reliable evidence. It should not
invent missing facts.

## Week 2 Target Response

Week 2 will extend the response shape as hybrid RAG features are introduced.
The target shape is:

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
  "trace": null
}
```

Target field meanings:

- `route`: routing decision from the intent router. Expected values are
  `structured_only`, `document_only`, `hybrid`, and `fallback`.
- `evidence[].evidence_id`: stable identifier for an evidence item inside one
  response.
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

The answer should remain conservative when `fallback=true`.

## Local Smoke Commands

```powershell
curl.exe -s http://127.0.0.1:8000/health
curl.exe -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"user_id":"u1","session_id":"s1","query":"退货政策是什么？"}'
```
