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
