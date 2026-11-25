# Backlog

See `PLAN.md` for the agreed design of the `harness tdd` loop.

- [x] Stop the scored refactor loop at `--max-passes`.
      Test: with scores that keep falling, the loop stops at the pass limit and keeps the last refactor; `make tests` passes.

- [ ] Check the score files and the score prompt in preflight.
      Test: `harness tdd` aborts when the target `.gitignore` does not ignore the two count files, and when the score prompt is missing; `make tests` passes.
