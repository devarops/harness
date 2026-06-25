# harness

Automated TDD cycles driven by specification verification.

## What it does

Given a project with acceptance criteria written as a qed spec, harness runs
automated Red-Green-Refactor cycles. Each cycle advances through a conveyor
belt of verification steps — tests must fail before they pass, and mutation
tests confirm the tests actually catch defects. Progress is scored and
tracked over time.

## How to use it

1. Write your acceptance criteria in a qed spec file (`.spec.toml`) at the
   root of your project.
2. Run `docker compose up` to start the harness container from your project
   directory.
3. The harness runs cycles automatically. You approve or reject each
   candidate change before it lands.
4. Review the score history to see whether quality is trending up.

## Before you start

- Docker — the harness runs inside a container and manages its own
  dependencies.
- qed — a command-line verification tool (install separately).
- Your project's CI pipeline should include `make tests`, `make mutants`,
  and `make check` targets.

## Run the project

```bash
make init        # Install dependencies and run the test suite
make tests       # Run the test suite
```
