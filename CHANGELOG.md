# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Entire project rewritten from a single bash script (`tdd.sh`) to a Python package (`harness/`) with flit packaging and Typer CLI.
- Approval testing methodology replaces the `pi`-based AI prompt loop.
- Development environment moved from standalone script to Docker Compose (`docker-compose.yml`, `Dockerfile`).

### Added

- `approval/` package at project root with four functions:
  - `printer(value, name)` — writes content to a golden master received file.
  - `reject(name)` — removes a received file.
  - `approve(name)` — promotes a received file to the approved golden master.
  - `review(name)` — returns a unified diff between approved and received files.
- `harness/` Python package with `__version__` (`0.1.0`) and `version()` function.
- Approval testing fixture (`approval`) in `tests/conftest.py` with auto-promote on first run and diff-on-mismatch behavior.
- Golden master directory `tests/approval/` with version golden master.
- `Makefile` with targets: `init`, `tests`, `check`, `format`, `linter`, `coverage`, `mutants`, `clean`.
- `pyproject.toml` with flit build configuration.
- `Dockerfile` and `docker-compose.yml` for containerized development.
- `LICENSE` (GPLv3), `.gitignore`, `.flake8`, `mypy.ini`.

### Removed

- `src/tdd.sh`, `src/refactor.sh`, `src/acceptance-to-html.sh` — bash prototypes replaced by Python modules (retained in git history).

## [0.1.0] - 2026-06-09

### Added

- `tdd.sh` — automated TDD cycle orchestrator that runs Red, Green, Refactor, and Acceptance phases via `pi --print` phase prompts.
- Pre-flight checks for clean working tree and `prd.json` existence.
- `fix()` function for rolling back cycle commits when tests fail post-cycle.
- `is_done()` completion check using AI `<promise>COMPLETE</promise>` signal and `prd.json` state scan.
- Logging to `log.txt` with per-cycle separation.
- Support for optional `max_iterations` argument (default 10), matching ralph.sh convention.

[Unreleased]: https://github.com/devarops/harness/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/devarops/harness/releases/tag/v0.1.0
