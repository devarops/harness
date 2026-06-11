# AGENTS.md — tdd.sh

## Repository purpose

Single-file shell script (`tdd.sh`) that orchestrates automated TDD cycles.
It is NOT a project under development — it is a tool used *by* other projects.

## Entry point

- `tdd.sh` — the only file. Run `./tdd.sh [max_iterations]` from a consuming project root.

## External dependencies (not in this repo)

- `pi` CLI at `~/.local/bin/pi` (AI coding assistant)
- Phase prompts at `$HOME/.config/opencode/commands/{red,green,refactor,acceptance}-afk.md`
- Docker container named `${PWD##*/}_ci`
- Consuming project provides a `Makefile` with targets: `init`, `tests`, `mutants`, `check`, `format`
- Consuming project provides `acceptance.json` at repo root (schema documented in `tdd.sh` header)

## Key internals

- `is_done()` — checks AI `<promise>COMPLETE</promise>` signal AND scans `acceptance.json` for remaining tasks
- All commands use `set -eo pipefail` — any failure is fatal
