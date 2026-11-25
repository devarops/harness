# Backlog

See `PLAN.md` for the agreed design of the `harness tdd` loop.

- [*] Gate the run at startup and at the inner exit.
      Test: `harness tdd` aborts before any prompt when the startup `make verify` fails; when it passes, `atdd-acceptance` runs first; after the refactor loop, `make tests` runs and aborts on failure, then `make verify` repeats the inner cycle on failure and returns to acceptance on pass; no make verify runs at the start of a pass and no make tests runs after the acceptance red; `make tests` passes.

- [ ] Hunt mutants after the green commit.
      Test: after a green commit, `harness tdd` runs `make mutants`; a zero exit skips the mutation prompts and runs the refactor loop; `make tests` passes.

- [ ] Kill one mutant and commit the test.
      Test: with a survivor, `afk-mutant-kill` leaves a test under `tests/` uncommitted and `afk-mutant-commit` commits it; harness aborts when the kill leaves no change or changes anything else, and when the commit is not tests-only; `make tests` passes.

- [ ] Stop the hunting loop at `--max-passes`.
      Test: with survivors that never clear, the hunt stops at the pass limit and the run aborts; `make tests` passes.
