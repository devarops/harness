---
description: Implement the smallest production change that makes the failing test pass.
---

We are in the Green phase of the local TDD loop. Read `.opencode/local-loop.md`
and follow it.

## Task

- Find the single `[*]` item and its `Test:` line.
- Verify that the working tree is clean.
- Run `make tests` and confirm that exactly one test fails. More or none:
  report and stop.
- Read the full text of the last few commit messages.
- Implement only what the failing test requires. Prefer the simplest solution,
  including a naive one.
- Do not modify the test, `TODO.md`, or `.opencode/`.
- Generalize only if a naive change breaks a passing test.
- Run `make tests` and confirm that all tests pass.
- Stage only the files the change requires, and commit:

✅ 🧪 <summary>

<how the change satisfies the test; why it is minimal; the lesson>

- Show `git diff HEAD~1` and offer to undo the commit.
