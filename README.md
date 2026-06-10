# tdd.sh

Automated TDD cycle orchestrator.

## What it does

`tdd.sh` drives a Red-Green-Refactor-Acceptance loop, running each phase as a focused AI prompt.
It keeps working code and undoes changes when tests break.
When all tasks are done, it runs mutation tests as a final quality check.

## How to use it

1. Define what you want to build in `prd.json` — list each feature as a task with concrete acceptance criteria.
2. Place one copy of `tdd.sh` in your project root.
3. Run `./tdd.sh` and watch it work through each task one cycle at a time.
4. Inspect `log.txt` afterward to see what happened in each phase.

If a cycle breaks the test suite, the script undoes the last changes and tries again. If all tasks are completed, it runs mutation tests and exits cleanly.

## Before you start

- Docker — the script runs tests inside a container.
- `pi` CLI — the AI assistant that executes each TDD phase.
- A `prd.json` file at your project root describing your tasks.

## Coming soon

- Better error messages when prerequisites are missing.
- Support for custom prompt directories.
