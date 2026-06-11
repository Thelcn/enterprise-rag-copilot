# Week 2 Upgrade Plan

Week 1 proved that the service can accept a chat request, retrieve policy
documents, return an answer, cite evidence, and fallback when evidence is weak.
Week 2 upgrades that naive RAG v0 into a small production-style hybrid RAG
prototype.

The goal is not to rewrite the project. The goal is to preserve the Week 1 main
path while adding clear routing, structured tools, stronger evidence handling,
fallback semantics, evaluation, tracing, and a small cache/load-test demo.

## Current Week 1 v0 Flow

```text
POST /chat
  -> ChatRequest validation
  -> ecommerce adapter loads markdown documents
  -> chunker splits documents into chunks
  -> keyword retriever selects evidence
  -> prompt builder formats query + evidence
  -> rule-based answer generator writes grounded answer
  -> ChatResponse returns answer, intent, evidence, fallback, trace_id
```

The current implementation is intentionally deterministic. It does not depend on
a real LLM, a hosted vector database, or an external service, which makes it easy
to test and review.

## What v0 Already Does Well

- Keeps `app/pipeline/` domain-agnostic.
- Keeps ecommerce loading behind `app/domains/ecommerce/adapter.py`.
- Returns an `evidence` list instead of answer-only output.
- Returns `fallback=true` when no retrieved evidence passes the score threshold.
- Exposes stable `GET /health` and `POST /chat` routes.
- Has automated tests for health, chat contract, loading, retrieval, and the RAG
  pipeline.

## v0 Shortcomings

- **Structured facts are missing.** Order status, refund status, and product
  information are precise facts, but v0 can only search policy documents.
- **Routing is too coarse.** The current `intent` is a simple label from the
  naive pipeline, not a real intent router with route decisions.
- **Hybrid questions are not supported.** A question such as "Can order
  ORD-1001 be returned?" needs both order facts and return-policy evidence.
- **Evidence is document-only.** The response cannot yet distinguish document
  evidence from structured tool evidence.
- **Fallback reasons are limited.** v0 can fallback on low retrieval confidence,
  but not on missing order IDs, unknown tool records, unsupported scenarios, or
  high-risk insufficient evidence.
- **Evaluation is not centralized.** There is no `evaluation/` dataset or
  repeatable runner for ecommerce cases.
- **Performance tracing is incomplete.** v0 returns a `trace_id`, but does not
  yet record intent, tool, retrieval, answer, and total latency stages.
- **No cache or load-test artifact exists.** Week 2 should add a small,
  reproducible demo instead of claimed performance numbers.

## Week 2 Target Architecture

```text
POST /chat
  -> intent_router decides intent, route, and required slots
  -> structured tools answer precise ecommerce facts when needed
  -> document retriever answers policy and knowledge-base questions
  -> evidence builder normalizes structured and document evidence
  -> fallback handler explains missing or unsafe answers
  -> answer generator uses only available evidence
  -> performance tracer records stage timings
  -> optional cache stores deterministic responses for repeated queries
```

Route targets:

- `structured_only`: order, refund, or product facts from ecommerce tools.
- `document_only`: policy, logistics, warranty, and FAQ content from documents.
- `hybrid`: structured facts plus document policy evidence.
- `fallback`: unknown intent, missing required slots, weak evidence, or
  unsupported scenarios.

## Boundary Rules

- `app/pipeline/` contains generic mechanisms: routing interface, retrieval,
  evidence building, fallback handling, tracing, and cache primitives.
- `app/domains/ecommerce/` contains ecommerce-specific schema, repository,
  tools, metadata rules, and prompts.
- `evaluation/` contains test cases, metrics, and evaluation runner code.
- `scripts/` contains operational utilities such as index build or load-test
  scripts.
- API routes should orchestrate existing components, not read ecommerce JSON
  files directly.

## Day-by-Day Plan

| Day | Scope | Expected Artifacts |
| --- | --- | --- |
| Day 1 | Review v0 and lock baseline | `docs/week2_upgrade_plan.md`, `docs/api.md`, `tests/test_week1_baseline.py` |
| Day 2 | Intent router and structured tools | ecommerce schema, repository, tools, intent-router tests |
| Day 3 | Metadata rules and document filtering | metadata rules, retriever/filter tests, failure-case updates |
| Day 4 | Evidence builder and hybrid response shape | normalized evidence, route-aware chat response, tests |
| Day 5 | Fallback handler | missing-slot, weak-evidence, unknown-intent fallbacks |
| Day 6 | Evaluation and performance tracing | `evaluation/` cases, eval runner, tracer docs |
| Day 7 | Cache, load test, and summary | cache demo, load-test script, `docs/performance.md`, `docs/week2_summary.md` |

## Risks And Review Gates

- Do not break the Week 1 `/chat` happy path while adding Week 2 fields.
- Do not put ecommerce business rules into generic pipeline modules.
- Do not invent performance numbers. Latency, hit rate, and load-test results
  must come from local scripts or logs.
- Do not make tests depend on a real LLM or hosted service.
- Do not answer high-risk or unsupported questions without evidence.
- Review each day for correctness, readability, maintainability, and
  evolvability before committing.

## Acceptance Checks For Day 1

- The upgrade plan maps concrete Week 2 modules to Day 2 through Day 7.
- `docs/api.md` explains current fields and target Week 2 fields.
- `tests/test_week1_baseline.py` verifies `/health`, `/chat` answer output, and
  `/chat` evidence output.
- Failure cases include examples that justify structured tools and hybrid RAG.
- No fake metrics or premature framework rewrites are introduced.
