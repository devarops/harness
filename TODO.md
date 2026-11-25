# Backlog

See `PLAN.md` for the agreed design of the `harness tdd` loop.

- [*] Continue the refactor loop only on a lower median.
      Test: with fake medians, a lower after median keeps the refactor and starts another attempt; an equal median keeps it and stops; a higher median resets to the pre-refactor commit with a clean tree and stops; no valid score keeps it and stops; `make tests` passes.

- [ ] Stop the scored refactor loop at `--max-passes`.
      Test: with scores that keep falling, the loop stops at the pass limit and keeps the last refactor; `make tests` passes.

- [ ] Check the score files and the score prompt in preflight.
      Test: `harness tdd` aborts when the target `.gitignore` does not ignore the two count files, and when the score prompt is missing; `make tests` passes.
