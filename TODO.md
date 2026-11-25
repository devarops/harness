# Backlog

See `PLAN.md` for the agreed design of the `harness tdd` loop.

- [*] Stop the hunting loop at `--max-passes`.
      Test: with survivors that never clear, the hunt stops at the pass limit and the run aborts; `make tests` passes.
