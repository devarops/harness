# Backlog

See `PLAN.md` for the agreed design of the `harness tdd` loop.

- [*] Drop the mutation prompts from harness.
      Test: harness invokes neither `afk-mutant-kill.md` nor `afk-mutant-commit.md`, and preflight checks only the score prompt; `make tests` passes.

- [ ] Use long options in the commands harness runs.
      Test: the container calls pass `make --dry-run` and the activation commits pass `git commit --message`; `make tests` passes.
