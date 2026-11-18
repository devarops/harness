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
- Read the Thorns around the Gold rule at
  https://blog.cleancoder.com/uncle-bob/2014/11/19/GoingForTheGold.html. The
  gold is the behavior the item's `Test:` line describes; its thorns are the
  exceptional, degenerate, and ancillary behaviors around it.
- Confirm that the test is necessary to the item's `Test:` line: the line could
  not be met without the behavior under test. Reject a test that is not
  necessary.
- Confirm that the test is the smallest increment toward the `Test:` line and
  does not close it in one step.
- Classify the test. If it is a gold test, reject it when you can name an
  uncovered thorn for the item, and say which thorn. Accept it when no uncovered
  thorn remains; judge coverage over the whole suite by content, not by which
  item wrote a test.
- On rejection, leave the tree untouched, report the reason, and stop for a
  human. Do not commit and do not name a next command.
- Stage only the test and its fixtures, and commit:

🛑 🧪 <expected behavior>

<the item and its Test line; the behavior the test specifies; why it fails now; what remains open; confirmation that no other test fails; the lesson>

- Report the commit hash and `git revert <hash>`. Do not start Green.
