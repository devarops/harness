# Backlog

See `PLAN.md` for the agreed design of the `harness tdd` loop.

- [*] Deselect the failing acceptance test from mutation.
      Test: at the mutation gate, a failing active criterion's pytest node is passed to `make mutants` as `ACTIVE`, and a passing one is not; `make tests` passes.

- [ ] Read the mutation verdict from the tool's results.
      Test: the gate counts the surviving mutants in the `make mutants` output, ignores timeouts, and keeps the cycle when the count is zero; `make tests` passes.

- [ ] Abort when the mutation suite cannot start.
      Test: a nonzero `make mutants` exit aborts the run instead of announcing a streak or resetting the cycle; `make tests` passes.

- [ ] Refuse a non-pytest acceptance test at the gate.
      Test: an active criterion whose verify command is not a pytest node aborts the gate with an unsupported-exclusion error; `make tests` passes.

- [ ] Check the mutation verdict in preflight.
      Test: preflight aborts when `make mutants` cannot start and when its results report a survivor before the first pass; `make tests` passes.
