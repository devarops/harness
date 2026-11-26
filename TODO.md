# Backlog

See `PLAN.md` for the agreed design of the `harness tdd` loop.

- [x] Replace the mutant hunt with the mutation gate.
      Test: after `afk-green`, a passing `make mutants` enters the refactor loop with the cycle's commits in place; a failing one announces the streak and does not enter it; `make tests` passes.

- [ ] Reset a rejected cycle to its base.
      Test: survivors record the commit before `afk-red` as the base, reset hard to it, remove the `afk-fail` and `afk-green` commits, keep the activation and the acceptance test, and clean untracked files; `make tests` passes.

- [ ] Recheck the mutation suite after the reset.
      Test: after the reset, a passing `make mutants` starts the next cycle at `afk-red` without a verify; a failing one aborts the run; `make tests` passes.

- [ ] Count the consecutive rejected cycles.
      Test: the streak rises once per rejected cycle, resets on a clean run, survives an outer pass that runs no unit cycle, and stops the run when it reaches `--max-passes`; `make tests` passes.

- [ ] Run the mutation suite in preflight.
      Test: preflight dry-runs `make --dry-run mutants`, aborts when the target is missing, then runs `make mutants` and aborts on survivors before the first pass; `make tests` passes.

- [ ] Drop the mutation prompts from harness.
      Test: harness invokes neither `afk-mutant-kill.md` nor `afk-mutant-commit.md`, and preflight checks only the score prompt; `make tests` passes.

- [ ] Use long options in the commands harness runs.
      Test: the container calls pass `make --dry-run` and the activation commits pass `git commit --message`; `make tests` passes.
