# AGENTS.md — harness

## Repository purpose

Python package that orchestrates automated TDD cycles using qed-spec verification.
This is NOT a project under development — it is a tool used *by* other projects.

## Architecture

Two Python packages at the repo root:

- `harness/` — production package (Typer CLI, TDD loops, scoring, spec merging)
- `approval/` — golden-master approval testing helper (sibling package, not inside harness/)

Both are installed via flit editable install (`pip install --editable .`).

## Entry points

- `harness/__init__.py` — exports `__version__` and `version()` function
- `approval/__init__.py` — public API: `printer`, `reject`, `approve`, `review`

## Development workflow

All commands run inside a Docker container:

```bash
make init        # Install + run tests in one step
make tests       # pytest --verbose
make check       # black + flake8 + mypy
make format      # black (auto-fix)
make linter      # pylint
make coverage    # pytest --cov + coverage report
make mutants     # mutmut mutation testing
make clean       # Remove caches and build artifacts
```

To run a single test file:

```bash
docker exec harness_ci pytest tests/test_approval.py --verbose
```

## Testing methodology

The project uses **approval testing**, not TDD. Golden master files live in `tests/approval/`.
The `conftest.py` provides an `approval` fixture that auto-promotes on first run and diffs on mismatch.

Each TDD cycle uses Red (`🛑 🧪`) / Green (`✅ 🧪`) / Refactor (`♻️`) commit prefixes.

## Approval module (`approval/`)

Four functions in `approval/__init__.py`:

- `printer(value, name)` — writes value to `tests/approval/<name>.received.txt`
- `reject(name)` — removes `tests/approval/<name>.received.txt`
- `approve(name)` — renames received → approved
- `review(name)` — returns unified diff string between approved and received

## Project structure

```
harness/
├── approval/         # Golden-master approval helper package
├── harness/          # Production package (Typer CLI)
├── tests/
│   ├── approval/     # Golden master files (.approved.txt)
│   ├── conftest.py   # approval() fixture
│   └── test_*.py     # Tests
├── src/              # Retired bash prototypes (keep for history)
├── pyproject.toml    # flit build config
└── Makefile          # Standard targets
```

## Key conventions

- Python 3.14 (python:latest Docker image)
- Approval testing (compare .received.txt vs .approved.txt)
- qed is an external binary (not a pip package) — not yet installed in Docker image
- Docstrings follow Google style
- All tests pass inside Docker: `docker exec harness_ci make tests`
- Version is `0.1.0` in `harness/__init__.py`
