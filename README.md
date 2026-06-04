# Enterprise RAG Copilot

Enterprise RAG Copilot is a transferable RAG service skeleton for enterprise
assistant workflows. The first demo domain is ecommerce after-sales support,
but the core application must stay domain-agnostic so it can later support
other domains such as HR, IT support, or internal knowledge bases.

This repository is not a one-off toy demo. Week 1 focuses on building a small,
reviewable, testable engineering foundation before adding retrieval logic.

## Week 1 Goals

- Create a FastAPI service with a stable project structure.
- Expose `GET /health` as the first operational endpoint.
- Define clear boundaries between API, configuration, generic RAG pipeline, and
  domain adapters.
- Keep dependencies minimal and add tests or manual verification for each
  feature.

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Health check:

```powershell
curl http://127.0.0.1:8000/health
```

Run tests:

```powershell
pytest
```

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

## Initial Project Structure

```text
app/
  main.py
  api/
    routes.py
  core/
    config.py
tests/
  test_health.py
```

The RAG pipeline and ecommerce domain folders will be added in later Week 1
tasks according to the execution plan.
