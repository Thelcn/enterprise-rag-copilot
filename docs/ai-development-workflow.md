# AI Development Workflow

This project uses Codex as a coding assistant, not as an unchecked committer.
AI output is a candidate implementation until Chenning reviews it.

## Daily Workflow

1. Read the day's task card.
2. List the files to modify and why.
3. Implement only the scoped task.
4. Add tests or manual verification.
5. Update learning notes in `.learnings/`.
6. Stop for human review.
7. Commit only after review.
8. Update `git_learning_notes.md` before each commit.

## Required Review Gates

Before commit, check:

- Does the implementation meet today's goal?
- Did the change stay inside the allowed file scope?
- Did `/health` and `/chat` contracts remain stable?
- Does answer generation use evidence rather than invention?
- Are fallback cases explicit?
- Do tests or curl commands reproduce the expected behavior?
- Are known failures or caveats documented?

## Boundaries

Codex may:

- Generate scoped candidate code.
- Add focused tests.
- Update documentation and learning notes.
- Run local verification commands.
- Prepare git commits after review.

Codex must not:

- Rewrite the whole repository in one step.
- Hide failures or remove tests to make a run pass.
- Add complex dependencies without explaining alternatives.
- Put ecommerce business rules inside the generic pipeline.
- Claim keyword fallback is semantic vector retrieval.
- Commit before review unless explicitly asked.

## Git Learning Notes

Every commit should update:

```text
.learnings/git_learning_notes.md
```

The entry should record:

- Commands used.
- What each command does.
- Commit message.
- Push result.
- Problems encountered.
- What to learn from the Git workflow.

## Failure Logs

Unexpected command failures, tool issues, or design mistakes should be logged in:

```text
.learnings/ERRORS.md
```

Project-level RAG limitations should be logged in:

```text
docs/failure_cases.md
```

## Testing Expectations

For code changes, run focused tests first, then all tests:

```powershell
python -m pytest path/to/test_file.py -q
python -m pytest -q
```

Manual API checks should use `curl.exe` on Windows with single quotes around JSON
bodies.
