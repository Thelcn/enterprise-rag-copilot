# Architecture

Enterprise RAG Copilot is a transferable RAG service skeleton. The Week 1 demo
domain is ecommerce after-sales support, but the core pipeline is intentionally
domain-agnostic.

## Goals

- Keep the API contract stable while internals evolve.
- Separate generic RAG pipeline code from ecommerce domain data and adapters.
- Preserve evidence, fallback, and trace fields from the first `/chat` version.
- Keep Week 1 runnable without external embedding services or vector databases.

## Runtime Flow

```text
POST /chat
  -> ChatRequest validation
  -> ecommerce document adapter
  -> RagPipeline
  -> KeywordRetriever
  -> build_prompt
  -> generate_answer
  -> ChatResponse
```

## Module Boundaries

### API Layer

Files:

- `app/main.py`
- `app/api/routes.py`

Responsibilities:

- Create the FastAPI app.
- Expose `/health` and `/chat`.
- Validate request/response schemas through FastAPI and Pydantic.
- Wire the Week 1 demo domain into the generic pipeline.

The API layer should not implement retrieval, chunking, or answer generation.

### Schema Layer

Files:

- `app/schemas/chat.py`
- `app/schemas/evidence.py`
- `app/schemas/trace.py`
- `app/schemas/document.py`

Responsibilities:

- Define stable request, response, evidence, trace, document, and chunk shapes.
- Keep API contracts explicit and testable.

Schemas should not contain business workflow logic.

### Core Pipeline

Files:

- `app/pipeline/document_loader.py`
- `app/pipeline/chunker.py`
- `app/pipeline/embedder.py`
- `app/pipeline/vector_store.py`
- `app/pipeline/retriever.py`
- `app/pipeline/prompt_builder.py`
- `app/pipeline/answer_generator.py`
- `app/pipeline/rag_pipeline.py`

Responsibilities:

- Load generic markdown documents.
- Split documents into chunks.
- Build a deterministic keyword fallback index.
- Retrieve evidence.
- Build prompts.
- Generate evidence-grounded responses.
- Return fallback when no reliable evidence exists.

The pipeline must not hard-code ecommerce rules such as refunds, logistics, or
warranty decisions.

### Domain Adapter

Files:

- `app/domains/ecommerce/adapter.py`

Responsibilities:

- Know where ecommerce demo policy documents live.
- Load ecommerce documents through the generic document loader.

Domain adapters may know domain paths and prompt additions, but they should not
control the FastAPI entrypoint or rewrite core pipeline behavior.

### Data Layer

Files:

- `data/ecommerce/docs/*.md`
- `data/ecommerce/mock/*.json`

Responsibilities:

- Store demo policy documents and mock structured data.
- Keep Python logic out of data files.

## Logging

`app/core/logging_config.py` configures standard Python logging.

The RAG pipeline logs stage-level metadata:

- `trace_id`
- `stage`
- `evidence_count`
- latency in milliseconds

It does not log full prompts or full user queries. Week 1 logging is intended
for local traceability, not production observability.

## Week 1 Capability

The current RAG v0 can:

- Load ecommerce policy markdown.
- Split documents into chunks.
- Build a keyword fallback index.
- Retrieve top-k evidence.
- Build a prompt.
- Generate a simple evidence-grounded answer.
- Return fallback for low-evidence questions.

Week 1 final verification on 2026-06-04:

- `python -m pytest -q`: `21 passed`.
- `/health`: returns service metadata.
- `/chat` with `退货政策是什么？`: returns evidence and `fallback=false`.
- `/chat` with an unrelated membership-points query: returns `fallback=true`.

## Known Limits

- Keyword fallback is not semantic retrieval.
- Answer generation is rule-based and template-like.
- `/chat` answers policy questions only; it does not inspect specific orders.
- Mock order/product JSON is not yet connected to a structured query tool.
- No production tracing, evaluation suite, reranking, or real deployment setup.
- Dockerfile exists, but Docker build/run still needs to be re-verified after
  Docker Desktop's Linux engine is available on the development machine.

## Week 2 Direction

- Add structured order/product lookup through SQLite or a tool interface.
- Add intent routing for policy, order status, logistics, refund, warranty, and
  mixed questions.
- Add metadata filtering for document type and policy scenario.
- Upgrade evidence building so SQL/tool results and document chunks share the
  same evidence list.
- Add evaluation cases and performance tracing.
