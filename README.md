# Enterprise RAG Copilot

Enterprise RAG Copilot is a transferable RAG service skeleton for enterprise
assistant workflows. The first demo domain is ecommerce after-sales support,
but the core application must stay domain-agnostic so it can later support
other domains such as HR, IT support, or internal knowledge bases.

This repository is not a one-off toy demo. Week 1 focuses on building a small,
reviewable, testable engineering foundation and a naive RAG v0 loop.

## Week 1 Goals

- Create a FastAPI service with a stable project structure.
- Expose `GET /health` and `POST /chat`.
- Load ecommerce policy documents through a domain adapter.
- Run a naive RAG v0 loop: load, chunk, retrieve, prompt, answer.
- Return evidence, fallback, and trace fields for every chat response.
- Keep dependencies minimal and preserve a deterministic keyword fallback.

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Health check:

```powershell
curl http://127.0.0.1:8000/health
```

Run tests:

```powershell
python -m pytest -q
```

Docker:

```powershell
docker build -t enterprise-rag-copilot:week1 .
docker run --rm -p 8000:8000 enterprise-rag-copilot:week1
```

Note: Docker CLI is installed on the current development machine, but the Week 1
Docker build could not be completed until Docker Desktop's Linux engine is
running. Local Python startup and tests are verified.

## Current API

`GET /health` returns service metadata:

```json
{
  "status": "ok",
  "service": "enterprise-rag-copilot",
  "version": "0.1.0",
  "environment": "development"
}
```

`POST /chat` runs the Week 1 naive RAG pipeline:

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"user_id":"u1","session_id":"s1","query":"退货政策是什么？"}'
```

Example response shape:

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
  "trace_id": "trace_..."
}
```

Fallback example:

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"user_id":"u1","session_id":"s1","query":"量子咖啡会员积分怎么兑换？"}'
```

```json
{
  "answer": "我没有识别出这个问题需要查询哪类企业知识或业务数据。",
  "intent": "unknown",
  "route": "fallback",
  "evidence": [],
  "fallback": true,
  "fallback_reason": "unknown_intent",
  "trace_id": "trace_..."
}
```

## Project Structure

```text
app/
  main.py
  api/
    routes.py
  core/
    config.py
    errors.py
    logging_config.py
  domains/
    ecommerce/
      adapter.py
      metadata_rules.py
      repository.py
      schema.py
      tools.py
  pipeline/
    document_loader.py
    chunker.py
    embedder.py
    evidence_builder.py
    fallback_handler.py
    intent_router.py
    vector_store.py
    retriever.py
    prompt_builder.py
    answer_generator.py
    rag_pipeline.py
  schemas/
    chat.py
    document.py
    evidence.py
    trace.py
data/
  ecommerce/
    docs/
    mock/
evaluation/
  ecommerce_cases.json
docs/
  contracts/
  design/
scripts/
  build_index.py
tests/
  test_health.py
  test_chat_contract.py
  test_document_loader.py
  test_ecommerce_tools.py
  test_evidence_builder.py
  test_fallback_handler.py
  test_intent_router.py
  test_metadata_filtering.py
  test_metadata_rules.py
  test_retriever.py
  test_rag_pipeline.py
  test_week1_baseline.py
  test_week2_chat_routes.py
```

## Week 1 Progress

- Day 1: FastAPI skeleton and `/health`.
- Day 2: Stable `/chat` Pydantic contract.
- Day 3: Ecommerce demo data and generic markdown document loader.
- Day 4: Chunking, keyword fallback index, and retriever.
- Day 5: Naive RAG pipeline connected to `/chat`.
- Day 6: Docker, logging, architecture docs, and AI workflow docs.
- Day 7: Full test/API verification, failure log, and Week 1 summary.

## Week 2 Roadmap

Week 2 upgrades the naive RAG v0 into a hybrid RAG engineering prototype while
preserving the Week 1 baseline.

- Day 1: Review v0, document the upgrade plan, and add baseline tests.
- Day 2: Add intent routing and ecommerce structured tools.
- Day 3: Add metadata rules and document filtering.
- Day 4: Normalize structured and document evidence for hybrid responses.
- Day 5: Centralize fallback handling and failure semantics.
- Day 6: Add evaluation cases, an evaluation runner, and performance tracing.
- Day 7: Add cache/load-test demo artifacts and write the Week 2 summary.

## Week 1 Verification

Completed on 2026-06-04:

```powershell
python -m pytest -q
```

Result:

```text
21 passed
```

Manual API checks:

```powershell
curl.exe -s http://127.0.0.1:8000/health
curl.exe -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"user_id":"u1","session_id":"s1","query":"退货政策是什么？"}'
curl.exe -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"user_id":"u1","session_id":"s1","query":"量子咖啡会员积分怎么兑换？"}'
```

Observed behavior:

- `/health` returned service metadata.
- The return-policy query returned `fallback=false` with evidence from `return_policy.md`.
- The unrelated membership-points query returned `fallback=true` with an empty evidence list.

## Design Notes

- `app/pipeline/` is generic RAG code and should not contain ecommerce business rules.
- `app/domains/ecommerce/` is the ecommerce adapter boundary.
- Keyword fallback is deterministic and testable, but it is not semantic embedding.
- The answer generator is rule-based in Week 1 and only organizes retrieved evidence.
- If evidence is missing or below threshold, `/chat` returns fallback instead of inventing an answer.
- Week 2 Day 5 centralizes fallback decisions and returns stable reason codes
  such as `missing_order_id`, `order_not_found`, `no_evidence`, and
  `high_risk_request`.

## Documentation

- API contract: `docs/contracts/query_api.md`
- Architecture: `docs/design/architecture.md`
- AI workflow: `docs/ai-development-workflow.md`
- RAG v0 failure cases: `docs/failure_cases.md`
- Week 1 summary: `notes/week1_summary.md`
- Failure log: `notes/failure_log.md`
