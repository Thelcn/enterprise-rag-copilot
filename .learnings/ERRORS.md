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
