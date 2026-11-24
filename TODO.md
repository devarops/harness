# Backlog

See `PLAN.md` for the agreed design of the `harness tdd` loop.

- [*] Implement `scoring.py` — three `afk-score` runs per version, `<score>` validation, the two count files, and the median.
      Test: with a fake score prompt, the scorer runs it three times at a commit and file set, keeps the valid `<score>` integers, appends them to the version's count file, and returns their median; `make tests` passes.

- [ ] Score each refactor attempt before and after.
      Test: after a refactor commit, `harness tdd` scores the pre-refactor commit and the new commit three times each on the files the commit touched, clears both count files first, and records the two medians; `make tests` passes.

- [ ] Continue the refactor loop only on a lower median.
      Test: with fake medians, a lower after median keeps the refactor and starts another attempt; an equal median keeps it and stops; a higher median resets to the pre-refactor commit with a clean tree and stops; no valid score keeps it and stops; `make tests` passes.

- [ ] Stop the scored refactor loop at `--max-passes`.
      Test: with scores that keep falling, the loop stops at the pass limit and keeps the last refactor; `make tests` passes.

- [ ] Check the score files and the score prompt in preflight.
      Test: `harness tdd` aborts when the target `.gitignore` does not ignore the two count files, and when the score prompt is missing; `make tests` passes.

- [ ] Implement `refactor_loop.py` — outer loop: `qed verify` → `scoring.py`.
