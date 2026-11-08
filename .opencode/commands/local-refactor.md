---
description: Apply one behavior-preserving refactoring and commit it.
---

We are in the Refactor phase of the local TDD loop. Read
`.opencode/local-loop.md` and every reference in
`~/.config/opencode/refactor-references.md`.

## Task

- Find the single `[*]` item and its `Test:` line.
- Verify that the working tree is clean.
- Run `make tests` and confirm that all tests pass. Any failure: report and
  stop.
- Read the full text of the last few commit messages.
- Identify safe, behavior-preserving refactorings. Name each with a name from
  Fowler's catalog; state its motivation, improvement, and trade-offs.
- Apply only the single most important one.
- Run `make tests`. If any test fails, undo with `git restore .` and stop; do
  not patch the refactoring.
- Stage only the refactored files, and commit:

♻ 🧪 <catalog name>

<rationale; improvement; how behavior is preserved; trade-offs; the lesson>

- Show `git diff HEAD~1` and offer to undo the commit.
