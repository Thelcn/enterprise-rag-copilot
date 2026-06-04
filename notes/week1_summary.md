# Week 1 Summary

Date: 2026-06-04

Project: `enterprise-rag-copilot`

## Completed

Week 1 turned the project from a PDF execution plan into a running FastAPI RAG
v0 service.

Completed milestones:

- Day 1: FastAPI skeleton, `/health`, config, Dockerfile, README, health test.
- Day 2: `ChatRequest`, `ChatResponse`, `Evidence`, trace ID, mock `/chat`, API contract tests.
- Day 3: Ecommerce mock orders/products, policy markdown docs, generic document loader, ecommerce adapter.
- Day 4: `Chunk`, chunker, deterministic keyword fallback, in-memory index, retriever tests.
- Day 5: `retrieve -> prompt -> answer -> ChatResponse`, `/chat` connected to naive RAG pipeline.
- Day 6: Docker context updates, logging setup, architecture doc, AI workflow doc, README refresh.
- Day 7: Full test/API verification, failure log, Week 1 summary, final docs cleanup.

## Current Capability

The app can run locally and serve:

- `GET /health`
- `POST /chat`

`/chat` currently:

- validates `user_id`, `session_id`, and `query`
- loads ecommerce policy documents
- chunks documents
- retrieves evidence with keyword fallback
- builds a prompt
- generates a simple rule-based evidence-grounded answer
- returns `answer`, `intent`, `evidence`, `fallback`, `fallback_reason`, and `trace_id`

## Verification

Full test suite:

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

Observed:

- `/health` returned stable service metadata.
- Return-policy query returned evidence and `fallback=false`.
- Unrelated membership-points query returned `fallback=true` and empty evidence.

## Git History

Current Week 1 commits:

```text
8f1592d chore: add docker logging and architecture docs
1cab260 feat: connect chat endpoint to naive rag pipeline
b719401 feat: add chunking and keyword retrieval fallback
8a0c441 feat: add ecommerce documents and loader
b2d1762 feat: define chat api contract
147e1cf chore: initialize rag copilot fastapi skeleton
```

This satisfies the Week 1 requirement for at least 5 RAG-related commits.

## Design Decisions

### Stable API Contract

`/chat` kept the Day 2 response fields when moving from mock mode to RAG v0.
This avoids breaking clients while internals evolve.

### Core Pipeline vs Domain Adapter

`app/pipeline/` stays generic. Ecommerce-specific document paths live in
`app/domains/ecommerce/adapter.py` and `data/ecommerce/`.

### Keyword Fallback

Week 1 uses deterministic keyword fallback instead of external embeddings. This
keeps the project runnable without API keys, network access, or vector database
services.

### Evidence First

The answer generator only organizes retrieved evidence. If evidence is missing,
the system returns fallback instead of inventing an answer.

## Known Limitations

- Keyword fallback is not semantic retrieval.
- Chunking is broad and can include weakly related evidence.
- Answer generation is rule-based and template-like.
- `/chat` cannot answer user-specific order status or refund eligibility yet.
- Mock orders/products are not connected to a structured tool.
- Docker build/run needs re-verification after Docker Desktop's Linux engine is available.
- No evaluation suite, reranking, metadata filters, or performance tracing beyond simple logs.

## Week 2 Plan

Priority order:

1. Add a structured data interface for orders/products, likely SQLite or a simple tool abstraction.
2. Add intent routing for policy, order status, logistics, refund, warranty, and mixed questions.
3. Add metadata filtering for `document_type`, scenario, and product category.
4. Upgrade evidence building so structured results and document chunks share one evidence list.
5. Add fallback rules for low score, missing order ID, unsupported scenario, and high-risk after-sales cases.
6. Add at least 30 evaluation cases covering structured, document, mixed, and failure questions.
7. Add performance tracing for intent, retrieval, structured lookup, answer generation, and total latency.

## Interview Summary

- I built a FastAPI-based RAG Copilot as an engineering service, not a standalone script.
- I preserved a transferable `core pipeline + domain adapter` architecture instead of hard-coding ecommerce rules into retrieval.
- I returned evidence, fallback, and trace fields from the first `/chat` contract so later evaluation and debugging can build on stable interfaces.
