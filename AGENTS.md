# AGENTS.md — tdd.sh

## Repository purpose

Single-file shell script (`tdd.sh`) that orchestrates automated TDD cycles.
It is NOT a project under development — it is a tool used *by* other projects.

## Entry point

- `tdd.sh` — the only file. Run `./tdd.sh [max_iterations]` from a consuming project root.

## External dependencies (not in this repo)

- `pi` CLI at `~/.local/bin/pi` (AI coding assistant)
- Phase prompts at `$HOME/.config/opencode/commands/{red,green,refactor,acceptance}.md`
- Docker container named `${PWD##*/}_ci`
- Consuming project provides a `Makefile` with targets: `init`, `tests`, `mutants`, `check`, `format`
- Consuming project provides `prd.json` at repo root (schema documented in `tdd.sh` header)

## Key internals

- `fix()` — rolls back commits with `git reset --hard HEAD~1` when tests fail post-cycle
- `is_done()` — checks AI `<promise>COMPLETE</promise>` signal AND scans `prd.json` for remaining tasks
- `CYCLE_HEAD` — recorded before each iteration as rollback safety bound
- All commands use `set -eo pipefail` — any failure is fatal
