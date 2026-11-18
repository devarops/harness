# Local TDD Loop

Shared rules for the `local-*` commands. Read this file before acting.

## Anchor

- Work from the repository root.
- `TODO.md` holds the work in play. Exactly one item is marked `[*]`, and its
  definition of done is the six-space `Test:` line below it.
- Zero or several marked items, or a missing `Test:` line, is misconfiguration.
  Report it and stop.
- Harness has no acceptance spec and no development container. Every check runs
  on the host with `make tests`.

## Vocabulary

- **Gold**: the behavior the in-play item's `Test:` line describes.
- **Thorns**: the behaviors around the gold — *exceptional* (input the gold
  should never see), *degenerate* (input that makes the gold do nothing), and
  *ancillary* (supporting behavior that is not the gold).
- **Gate**: an uncovered thorn comes before any gold test. Red writes thorns
  until it can name none that the suite leaves uncovered; Fail re-derives the
  same judgment and rejects a gold test while one remains. Coverage is judged
  over the whole suite by content, not by which item wrote a test.
- The end of the thorns is a judgment, not a rule. A gold test is proper once
  no uncovered thorn remains, and it need not close the `Test:` line.
- A rejection stops for a human. The loop does not retry on its own.

## Boundaries

- A phase starts from the state the previous phase left. Red, green, refactor,
  and acceptance start on a clean tree; fail starts with only the new test
  uncommitted.
- Run `make tests` before acting and after writing. Report the exact result.
- Only Red writes tests. Never modify an existing test to make production code
  pass.
- Apply one increment only: one failing test, one minimal implementation, one
  refactoring.
- Do not start the next phase. Report it and stop.

## Commits

- Each phase stages only its own files and uses the format its command defines.
  No Conventional Commits prefixes.
- Report the commit hash and how to undo it.

## State

- `TODO.md` is the only loop state. Do not create result files, status files, or
  counters.
