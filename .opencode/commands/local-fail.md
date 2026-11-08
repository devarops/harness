---
description: Re-validate the uncommitted failing test and commit it.
---

We are in the Fail sub-phase of the local TDD loop. Read
`.opencode/local-loop.md` and follow it.

## Task

- Find the single `[*]` item and its `Test:` line.
- Run `make tests` and confirm that exactly one test fails.
- If the tree is clean and exactly one test fails, the Red is committed: report
  that the next command is `local-green` and stop.
- Confirm that the only uncommitted changes are the new test and its fixtures.
  Anything else: list it and stop.
- Confirm that the failure is an assertion or an interface absence inside the
  test body. A collection, module-level import, or syntax error is not a valid
  Red.
- Confirm that the test is the smallest increment toward the `Test:` line and
  does not close it in one step.
- Stage only the test and its fixtures, and commit:

🛑 🧪 <expected behavior>

<the item and its Test line; the behavior the test specifies; why it fails now; what remains open; confirmation that no other test fails; the lesson>

- Report the commit hash and `git revert <hash>`. Do not start Green.
