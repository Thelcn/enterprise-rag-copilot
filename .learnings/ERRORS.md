# Error Log

## [ERR-20260604-001] python_venv_ensurepip

**Logged**: 2026-06-04T15:44:00+08:00
**Priority**: medium
**Status**: handled
**Area**: infra

### Summary
Creating the project virtual environment failed during `ensurepip`.

### Error
```text
Error: Command '['G:\\港城莞\\Agent_study\\enterprise-rag-copilot\\.venv\\Scripts\\python.exe', '-m', 'ensurepip', '--upgrade', '--default-pip']' returned non-zero exit status 1.
```

### Context
- Command attempted: `python -m venv .venv`
- Workspace: `G:\港城莞\Agent_study\enterprise-rag-copilot`
- Python: `C:\Users\hp\AppData\Local\Programs\Python\Python310\python.exe`

### Suggested Fix
Inspect the partially created `.venv` and try running `.venv\Scripts\python.exe -m ensurepip --upgrade --default-pip` directly. If that fails, use the base Python environment with explicit dependency installation or recreate the venv after clearing the partial directory.

### Resolution
Running `.venv\Scripts\python.exe -m ensurepip --upgrade --default-pip` reproduced the permissions issue. Day 1 verification continued by installing dependencies into the current user Python environment with `python -m pip install -r requirements.txt --user`, then running `python -m pytest` and `curl.exe` against the live service.

### Metadata
- Reproducible: unknown
- Related Files: requirements.txt

---

## [ERR-20260613-001] random_evidence_id_breaks_retriever_determinism

**Logged**: 2026-06-13T20:00:00+08:00
**Priority**: low
**Status**: handled
**Area**: tests

### Summary
Day4 added `Evidence.evidence_id` with a random default, which broke an existing deterministic retriever test.

### Error
```text
FAILED tests/test_retriever.py::test_keyword_fallback_is_deterministic
AssertionError: assert first == second
```

### Context
- Command attempted: `python -m pytest -q`
- Test: `test_keyword_fallback_is_deterministic`
- Cause: two identical retrieval calls returned equivalent evidence content but different randomly generated `evidence_id` values.

### Suggested Fix
Generate document evidence IDs from stable fields such as evidence type, source, and content when building retriever evidence.

### Resolution
Updated `app/pipeline/retriever.py` to set `evidence_id=build_evidence_id("document", source, content)` and `evidence_type="document"` for retrieved evidence.

### Metadata
- Reproducible: yes
- Related Files: app/schemas/evidence.py, app/pipeline/retriever.py, app/pipeline/evidence_builder.py, tests/test_retriever.py

---

## [ERR-20260613-002] fallback_reason_test_assumption_low_score

**Logged**: 2026-06-13T14:52:00+08:00
**Priority**: low
**Status**: handled
**Area**: tests

### Summary
Day5 fallback pipeline test initially expected `no_evidence`, but the keyword retriever returned weak candidates that were filtered out by the score threshold, so the correct reason was `low_retrieval_score`.

### Error
```text
FAILED tests/test_rag_pipeline.py::test_rag_pipeline_fallbacks_when_no_evidence_matches
AssertionError: assert 'low_retrieval_score' == 'no_evidence'
```

### Context
- Command attempted: `python -m pytest tests\test_week2_chat_routes.py tests\test_rag_pipeline.py -q`
- Query: `量子咖啡会员积分怎么兑换？`
- Cause: Chinese keyword tokenization can produce very weak lexical matches even when the query is outside the ecommerce policy domain.

### Suggested Fix
When testing fallback reasons, distinguish "no retrieval candidates" from "retrieval candidates exist but all are below the minimum score." Use `low_retrieval_score` for the latter.

### Resolution
Updated the RAG pipeline test to expect `errors.LOW_RETRIEVAL_SCORE` and changed the test name to `test_rag_pipeline_fallbacks_when_retrieval_score_is_low`.

### Metadata
- Reproducible: yes
- Related Files: app/pipeline/rag_pipeline.py, app/pipeline/fallback_handler.py, tests/test_rag_pipeline.py

---

## [ERR-20260613-003] evaluation_case_exposed_intent_priority_bug

**Logged**: 2026-06-13T15:22:00+08:00
**Priority**: medium
**Status**: handled
**Area**: tests

### Summary
Week2 Day6 evaluation case `D008` expected a shipping-time policy question to route to `logistics`, but the intent router matched the broader order-status rule first and returned `missing_order_id`.

### Error
```text
case_id=D008
query=发货时间是什么？
expected=(logistics, document_only, fallback=false)
actual=(order_status, fallback, fallback=true, fallback_reason=missing_order_id)
```

### Context
- Command attempted: `python -m evaluation.run_eval --cases evaluation\ecommerce_cases.json --out evaluation\eval_report.json --markdown-out evaluation\eval_report.md`
- Cause: `order_status` included the broad keyword `发货`, while `logistics` included the more specific keyword `发货时间`. The broader rule was evaluated first.

### Suggested Fix
Put the more specific logistics rule before the broad order-status rule, then add a focused intent-router test for `发货时间是什么？`.

### Resolution
Moved the logistics `IntentRule` above `order_status` in `app/domains/ecommerce/adapter.py` and added `test_router_prefers_logistics_policy_for_shipping_time_question`.

### Metadata
- Reproducible: yes
- Related Files: app/domains/ecommerce/adapter.py, tests/test_intent_router.py, evaluation/ecommerce_cases.json

---

## [ERR-20260613-004] manual_hybrid_query_routed_to_refund

**Logged**: 2026-06-13T15:28:00+08:00
**Priority**: medium
**Status**: handled
**Area**: backend

### Summary
The Day6 manual hybrid query `订单 EC1001 的退款状态和退货政策是什么？` routed to `refund` and fell back with `missing_refund_id` instead of using the order id plus return-policy evidence.

### Error
```text
query=订单 EC1001 的退款状态和退货政策是什么？
actual_intent=refund
actual_route=fallback
fallback_reason=missing_refund_id
```

### Context
- Command attempted: manual `curl.exe` check against local `/chat`.
- Cause: the hybrid rule did not include `退货政策`, so the refund rule matched `退款状态` first.

### Suggested Fix
Include `退货政策` in the hybrid rule when an order id is present, then add both router and evaluation coverage for the manual Day6 query.

### Resolution
Added `退货政策` to the hybrid intent keywords, added a focused router test, and added evaluation case `H006`.

### Metadata
- Reproducible: yes
- Related Files: app/domains/ecommerce/adapter.py, tests/test_intent_router.py, evaluation/ecommerce_cases.json

---

## [ERR-20260611-001] metadata_filtering_test_assumption

**Logged**: 2026-06-11T19:00:00+08:00
**Priority**: low
**Status**: handled
**Area**: tests

### Summary
Week2 Day3 metadata filtering tests assumed a semantically wrong document type would return no evidence, but the keyword retriever can still match shared Chinese characters.

### Error
```text
FAILED tests/test_metadata_filtering.py::test_metadata_filter_can_return_empty_without_crashing
AssertionError: assert [Evidence(source='return_policy.md', ...)] == []

FAILED tests/test_metadata_filtering.py::test_metadata_filter_can_fallback_to_unfiltered_retrieval
AssertionError: assert 'return_policy.md' == 'warranty_policy.md'
```

### Context
- Command attempted: `python -m pytest tests\test_metadata_rules.py tests\test_metadata_filtering.py -q`
- Query: `耳机保修多久？`
- Filter used by the first test: `{"document_type": "return_policy"}`
- Cause: the deterministic keyword fallback tokenizes Chinese text into single-character and bigram tokens. Even a semantically wrong document can match shared characters after the policy docs were expanded with metadata/example text.

### Suggested Fix
Use a nonexistent document type when testing "filtered search has no candidates", and separately test correct document-type filters for return/warranty/logistics precision.

### Resolution
Updated the empty-result and fallback tests to use `{"document_type": "nonexistent_policy"}`. Correct document-type precision remains covered by return-policy and warranty-policy filter tests.

### Metadata
- Reproducible: yes
- Related Files: tests/test_metadata_filtering.py, app/pipeline/embedder.py

---

## [ERR-20260604-006] docker_build_daemon_unavailable

**Logged**: 2026-06-04T17:20:00+08:00
**Priority**: medium
**Status**: pending
**Area**: infra

### Summary
Day 6 Docker build verification could not complete because Docker Desktop's Linux engine was not available.

### Error
First attempt:

```text
ERROR: open C:\Users\hp\.docker\buildx\.lock: Access is denied.
```

Second attempt with elevated permission:

```text
ERROR: failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine; check if the path is correct and if the daemon is running: open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.
```

### Context
- Command attempted: `docker build -t enterprise-rag-copilot:week1 .`
- Docker CLI was installed: `Docker version 29.3.1`
- The Docker daemon or Docker Desktop Linux engine was not reachable.

### Suggested Fix
Start Docker Desktop and ensure the Linux engine is running, then rerun:

```powershell
docker build -t enterprise-rag-copilot:week1 .
docker run --rm -p 8000:8000 enterprise-rag-copilot:week1
```

### Metadata
- Reproducible: yes
- Related Files: Dockerfile, .dockerignore

---

## [ERR-20260604-005] git_learning_notes_patch_context

**Logged**: 2026-06-04T16:50:00+08:00
**Priority**: low
**Status**: handled
**Area**: docs

### Summary
Updating `git_learning_notes.md` for Day 4 initially failed because the patch context did not match the file content exactly.

### Error
```text
apply_patch verification failed: Failed to find expected lines
```

### Context
- Operation attempted: append Day 4 Git learning notes before committing Day 4
- File: `.learnings/git_learning_notes.md`
- Cause: the patch used an expected context line that did not match the actual markdown content exactly.

### Suggested Fix
Read the tail of the file first and append using exact nearby context, or append at the end of the document with minimal context.

### Resolution
Inspected the actual tail of `git_learning_notes.md`, then appended the Day 4 Git learning entry using the correct end-of-file context.

### Metadata
- Reproducible: no
- Related Files: .learnings/git_learning_notes.md

---

## [ERR-20260604-004] powershell_curl_json_quoting

**Logged**: 2026-06-04T16:25:00+08:00
**Priority**: low
**Status**: handled
**Area**: tests

### Summary
A manual `curl.exe` verification for `POST /chat` sent invalid JSON because the PowerShell command used fragile escaping.

### Error
```text
{"detail":[{"type":"json_invalid","loc":["body",1],"msg":"JSON decode error","input":{},"ctx":{"error":"Expecting property name enclosed in double quotes"}}]}
```

### Context
- Command attempted: `curl.exe -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d "...escaped JSON..."`
- Endpoint: `POST /chat`
- The API was running, but the JSON body received by FastAPI was malformed.

### Suggested Fix
Use PowerShell single quotes around the JSON body for `curl.exe`, for example:

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"user_id":"u1","session_id":"s1","query":"退货政策是什么？"}'
```

### Resolution
Reran the manual verification with PowerShell single quotes around the JSON body. The valid `/chat` request returned the expected mock `ChatResponse`, and the blank query request returned HTTP `422`.

### Metadata
- Reproducible: yes
- Related Files: tests/test_chat_contract.py

---

## [ERR-20260604-003] git_add_index_lock_permission

**Logged**: 2026-06-04T16:07:00+08:00
**Priority**: medium
**Status**: handled
**Area**: infra

### Summary
`git add .` failed because Git could not create `.git/index.lock`.

### Error
```text
fatal: Unable to create 'G:/港城莞/Agent_study/enterprise-rag-copilot/.git/index.lock': Permission denied
```

### Context
- Command attempted: `git add .`
- Workspace: `G:\港城莞\Agent_study\enterprise-rag-copilot`
- Repository had just been initialized after a previous `.git/config.lock` issue.

### Suggested Fix
Retry the Git staging operation with elevated filesystem permission. If the lock file exists after failure, remove only the stale `.git\index.lock` file and retry.

### Resolution
Retried `git add .` with elevated filesystem permission. Staging completed successfully. Git emitted Windows LF-to-CRLF warnings only; no file staging failure remained.

### Metadata
- Reproducible: unknown
- Related Files: .git/index.lock

---

## [ERR-20260604-002] git_init_config_lock

**Logged**: 2026-06-04T16:05:00+08:00
**Priority**: medium
**Status**: handled
**Area**: infra

### Summary
`git init` failed while writing `.git/config` because a `config.lock` file could not be removed.

### Error
```text
warning: unable to unlink 'G:/港城莞/Agent_study/enterprise-rag-copilot/.git/config.lock': Invalid argument
error: could not write config file G:/港城莞/Agent_study/enterprise-rag-copilot/.git/config: Permission denied
fatal: could not set 'core.repositoryformatversion' to '0'
```

### Context
- Command attempted: `git init`
- Workspace: `G:\港城莞\Agent_study\enterprise-rag-copilot`
- Result: partial `.git` directory was created but repository initialization did not complete.

### Suggested Fix
Remove the stale `.git\config.lock` file if it exists, then rerun `git init`.

### Resolution
Removed `.git\config.lock` and reran `git init` with elevated filesystem permission. Repository initialization completed successfully.

### Metadata
- Reproducible: unknown
- Related Files: .git/config.lock

---
