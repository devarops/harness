# DOCS.md — tdd.sh

## tdd.sh [max_iterations]

Orchestrates automated TDD cycles using `pi` phase prompts, Docker-based test execution, and `acceptance.json` task tracking.

- Parameters:
  - `max_iterations`: integer, optional. Maximum number of TDD cycles to run before giving up. Default: `10`.

- Returns:
  - Exit code `0`: all tasks in `acceptance.json` completed (`gold` states: no `current`, no `backlog`, no `passes: false`).
  - Exit code `1`: max iterations reached without completing all tasks, or a fatal error occurred (`set -eo pipefail`).

- Errors:
  - Working tree is dirty: script aborts before any action.
  - `acceptance.json` missing at repo root: script prints schema reference and aborts.
  - Any command failure (`pi`, `docker exec make`, `git reset`, `jq`) exits immediately with the failing command's exit code.

- Notes:
  - Consuming project must provide `Makefile` targets: `init`, `tests`, `mutants`, `check`, `format`.
  - Docker container name is inferred as `${PWD##*/}_ci`.
  - Phase prompts are read from `$HOME/.config/opencode/commands/`.
  - Log output accumulates in `log.txt` at the repo root.
