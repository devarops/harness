# harness

Tooling for developing application repositories that follow the qed acceptance
standard. The public interface is the `harness` Typer CLI; `harness tdd` runs
the ATDD outer loop and the TDD inner loop against a conforming repository.

Harness itself is not an application repository and does not carry `specs/`.
The bash prototype in `src/` is the behavioral reference and will be retired.
See [PLAN.md](PLAN.md) for the input contract and loop design.
