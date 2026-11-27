# Backlog

See `PLAN.md` for the agreed design of the `harness tdd` loop.

- [*] Count the consecutive rejected cycles.
      Test: the streak rises once per rejected cycle, resets on a clean run, and stops the run when it reaches `--max-passes`; `make tests` passes.

- [ ] Run the mutation suite in preflight.
      Test: preflight dry-runs `make --dry-run mutants`, aborts when the target is missing, then runs `make mutants` and aborts on survivors before the first pass; `make tests` passes.

- [ ] Drop the mutation prompts from harness.
      Test: harness invokes neither `afk-mutant-kill.md` nor `afk-mutant-commit.md`, and preflight checks only the score prompt; `make tests` passes.

- [ ] Use long options in the commands harness runs.
      Test: the container calls pass `make --dry-run` and the activation commits pass `git commit --message`; `make tests` passes.
