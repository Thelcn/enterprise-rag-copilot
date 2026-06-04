# Week 1 Failure Log

This log records concrete Week 1 failures and decisions. It is intentionally
plain: the goal is to make bugs and environment risks reviewable instead of
hidden.

## Day 1 - 2026-06-04

### Bug / Failure Summary

The project virtual environment failed during `ensurepip`.

### Input

```powershell
python -m venv .venv
```

### Expected

A project-local `.venv` with working Python and pip.

### Actual

The command failed while running `ensurepip`. A direct retry inside `.venv`
also failed with Windows access denied while installing pip metadata.

### Hypothesis

The workspace or Windows filesystem permissions blocked pip metadata writes
inside the partially created `.venv`.

### Fix / Decision

For Week 1 verification, dependencies were installed into the current user
Python environment:

```powershell
python -m pip install -r requirements.txt --user
```

The `.venv` issue remains an environment cleanup item.

### Test Added / Verification

```powershell
python -m pytest tests/test_health.py -q
curl.exe http://127.0.0.1:8000/health
```

### Interview Note

I separated environment failure from application failure and kept verification
moving through an explicit fallback installation path.

## Day 1 - 2026-06-04

### Bug / Failure Summary

Initial Git setup hit Windows lock/permission issues.

### Input

```powershell
git init
git add .
```

### Expected

Git repository initialization and staging should complete.

### Actual

Git failed on `.git/config.lock` and later `.git/index.lock` permission issues.

### Hypothesis

Git was left in a partial initialization state and the workspace required
elevated permission to write Git internal files.

### Fix / Decision

Removed the stale `.git/config.lock`, reran `git init`, and used elevated
permission for staging/commit/push operations when required.

### Test Added / Verification

```powershell
git status --short
git log --oneline --decorate -n 3
git push -u origin main
```

### Interview Note

I treated Git locks as repository-state problems, removed only confirmed stale
lock files, and avoided destructive Git resets.

## Day 2 - 2026-06-04

### Bug / Failure Summary

Manual `curl.exe` verification sent malformed JSON because of PowerShell
quoting.

### Input

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d "...escaped JSON..."
```

### Expected

FastAPI should receive a valid JSON request body.

### Actual

FastAPI returned a JSON decode error.

### Hypothesis

The command used fragile escaping for JSON inside PowerShell.

### Fix / Decision

Use single quotes around the JSON body:

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"user_id":"u1","session_id":"s1","query":"退货政策是什么？"}'
```

### Test Added / Verification

The corrected command returned a structured `ChatResponse`; blank query returned
HTTP `422`.

### Interview Note

Manual API verification is part of the contract; command syntax must be as
reproducible as code.

## Day 4 - 2026-06-04

### Bug / Failure Summary

`retriever.py` initially had a typo in an import while being created.

### Input

Creating Day 4 retrieval code.

### Expected

Retriever should import `split_documents` from `app.pipeline.chunker`.

### Actual

The first file draft used an incorrect module name and was immediately fixed.

### Hypothesis

Simple typing error during file creation.

### Fix / Decision

Corrected the import to:

```python
from app.pipeline.chunker import split_documents
```

### Test Added / Verification

```powershell
python -m pytest tests/test_retriever.py -q
```

### Interview Note

Small module-boundary mistakes are caught quickly when each pipeline component
has focused tests.

## Day 6 - 2026-06-04

### Bug / Failure Summary

Docker build could not complete because Docker Desktop's Linux engine was not
available.

### Input

```powershell
docker build -t enterprise-rag-copilot:week1 .
```

### Expected

Docker should build the Week 1 image from the Dockerfile.

### Actual

First attempt hit a buildx lock permission issue. Elevated retry failed because
the Docker API pipe for `dockerDesktopLinuxEngine` did not exist.

### Hypothesis

Docker CLI is installed, but Docker Desktop or its Linux engine is not running.

### Fix / Decision

Document the environment blocker and verify the app through local Python
startup, tests, and curl. Docker build/run should be rechecked after Docker
Desktop is started.

### Test Added / Verification

```powershell
python -m pytest -q
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
curl.exe -s http://127.0.0.1:8000/health
```

### Interview Note

I did not claim Docker verification passed. I recorded the infrastructure
blocker and preserved a reproducible command for the next environment check.

## Week 1 Recurring Warning - 2026-06-04

### Bug / Failure Summary

`pytest` repeatedly emitted cache path warnings on this Windows workspace.

### Input

```powershell
python -m pytest -q
```

### Expected

Tests should run and optionally write pytest cache.

### Actual

Tests passed, but pytest warned that it could not create a cache path under the
workspace.

### Hypothesis

The workspace path or filesystem behavior interferes with pytest cache file
creation.

### Fix / Decision

No code change. The warning does not affect test correctness. Keep using
`python -m pytest -q` and treat the warning as local environment noise unless it
starts blocking tests.

### Test Added / Verification

Week 1 final verification:

```text
21 passed
```

### Interview Note

Warnings should be triaged, not ignored blindly. This one was separated from
test failures because all assertions passed.
