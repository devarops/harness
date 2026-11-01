# harness

Tooling for developing application repositories that follow the qed acceptance
standard. The public interface is the `harness` Typer CLI; the planned
`harness tdd` command runs red, green, refactor, and acceptance passes against a
conforming repository.

Harness itself is not an application repository and does not carry `specs/`.
See [PLAN.md](PLAN.md) for the input contract and loop design.
