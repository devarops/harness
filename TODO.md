# Backlog

See `PLAN.md` for the agreed design of the `harness tdd` loop.

- [x] Hunt mutants after the green commit.
      Test: after a green commit, `harness tdd` runs `make mutants`; a zero exit skips the mutation prompts and runs the refactor loop; `make tests` passes.

- [ ] Kill one mutant and commit the test.
      Test: with a survivor, `afk-mutant-kill` leaves a test under `tests/` uncommitted and `afk-mutant-commit` commits it; harness aborts when the kill leaves no change or changes anything else, and when the commit is not tests-only; `make tests` passes.

- [ ] Stop the hunting loop at `--max-passes`.
      Test: with survivors that never clear, the hunt stops at the pass limit and the run aborts; `make tests` passes.
