# Backlog

See `PLAN.md` for the agreed design of the `harness tdd` loop.

- [x] Refuse a non-pytest acceptance test at the gate.
      Test: an active criterion whose verify command is not a pytest node aborts the gate with an unsupported-exclusion error; `make tests` passes.

- [ ] Check the mutation verdict in preflight.
      Test: preflight aborts when `make mutants` cannot start and when its results report a survivor before the first pass; `make tests` passes.
