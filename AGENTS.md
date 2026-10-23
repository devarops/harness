# AGENTS.md — harness

## Repository purpose

Repository for harness, a tool for automated TDD cycles driven by specifications.

## Public interface

The public interface is the `harness` Typer CLI.

## Architecture

- `harness/` — Python package; `__init__.py` exposes `__version__`.
- `src/` — disposable bash prototypes that inform the Python implementation.
- `tests/` — pytest tests.
- `examples/`, `schemas/` — sample acceptance file and schemas used by the prototypes.
- `Makefile`, `Dockerfile`, `docker-compose.yml` — development entry points.

## Development workflow

Run commands in the Compose container:

```bash
docker compose run --rm devarops make init
docker compose run --rm devarops make tests
docker compose run --rm devarops make check
docker compose run --rm devarops make format
docker compose run --rm devarops make linter
docker compose run --rm devarops make coverage
docker compose run --rm devarops make mutants
docker compose run --rm devarops make clean
```

Run a single test file:

```bash
docker compose run --rm devarops pytest tests/test_harness.py --verbose
```

## Project structure

```
harness/
├── harness/
│   └── __init__.py
├── src/
├── tests/
├── examples/
├── schemas/
├── Makefile
├── Dockerfile
└── docker-compose.yml
```

## Key conventions

- The Docker image uses `python:latest` (3.14 at the time of writing); `pyproject.toml` declares `>=3.9`.
- flit packaging with `module = "harness"`; `make install` installs it in editable mode.
- Version is `0.1.0` in `harness/__init__.py`.
- qed runs in the repository the CLI operates on, not in this development image.
- Docstrings follow Google style.
