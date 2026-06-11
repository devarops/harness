# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Renamed `prd.json` to `acceptance.json` throughout the project: data file, schema file, example file, script references, and documentation.

## [0.1.0] - 2026-06-09

### Added

- `tdd.sh` — automated TDD cycle orchestrator that runs Red, Green, Refactor, and Acceptance phases via `pi --print` phase prompts.
- Pre-flight checks for clean working tree and `prd.json` existence.
- `fix()` function for rolling back cycle commits when tests fail post-cycle.
- `is_done()` completion check using AI `<promise>COMPLETE</promise>` signal and `prd.json` state scan.
- Logging to `log.txt` with per-cycle separation.
- Support for optional `max_iterations` argument (default 10), matching ralph.sh convention.

[Unreleased]: https://github.com/snarktank/tdd/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/snarktank/tdd/releases/tag/v0.1.0
