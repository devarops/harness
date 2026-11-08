---
description: Write exactly one failing unit test toward the in-progress TODO item.
---

We are in the Red phase of the local TDD loop. Read `.opencode/local-loop.md`
and follow it.

## Task

- Find the single `[*]` item and its `Test:` line.
- Verify that the working tree is clean.
- Read `git log --patch --max-count 8` for the lessons and the current position.
- Run `make tests`. If a test already fails, report it and stop: the Red test
  is committed and the next command is `local-green`.
- Compare the suite's observable behavior with the gap between the repository
  and the `Test:` line.
- Choose the next smallest behavioral increment. Prefer an exceptional,
  degenerate, or ancillary behavior before the core.
- Write exactly one failing unit test: one assertion, minimal setup, no extra
  structure. Put it under `tests/`.
- Do not modify existing tests, production code, `TODO.md`, or `.opencode/`.
- Run `make tests` and confirm that exactly one test fails.
- The failure must be an assertion or an interface absence inside the test
  body. A failure during collection, such as a module-level import or syntax
  error, is not a valid Red.
- Leave the test uncommitted. Report its path, the expected failure, and that
  the next command is `local-fail`.
