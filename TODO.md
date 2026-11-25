# Backlog

See `PLAN.md` for the agreed design of the `harness tdd` loop.

- [*] Kill one mutant and commit the test.
      Test: with a survivor, `afk-mutant-kill` leaves a test under `tests/` uncommitted and `afk-mutant-commit` commits it; harness aborts when the kill leaves no change or changes anything else, and when the commit is not tests-only; `make tests` passes.

- [ ] Stop the hunting loop at `--max-passes`.
      Test: with survivors that never clear, the hunt stops at the pass limit and the run aborts; `make tests` passes.
