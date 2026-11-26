# Backlog

See `PLAN.md` for the agreed design of the `harness tdd` loop.

- [*] Verify at the start of the inner loop.
      Test: after `atdd-red`, a passing `make verify` returns to acceptance without a unit prompt; a failing verify runs a cycle, then `make tests`, and verifies again; `make tests` passes.
