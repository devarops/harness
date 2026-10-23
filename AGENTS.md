# AGENTS.md — harness

## Repository purpose

Repository for harness, a tool for automated TDD cycles driven by specifications.

## Public interface

The public interface is the `harness` Typer CLI.

## Architecture

- `harness/` — Python package; `__init__.py` exposes `__version__`; `cli.py` defines the Typer app and the `version` command.
- `src/` — disposable bash prototypes that inform the Python implementation.
- `tests/` — pytest tests.
- `examples/`, `schemas/` — sample acceptance file and schemas used by the prototypes.
- `Makefile`, `Dockerfile`, `docker-compose.yml`, `pyproject.toml` — development and packaging entry points.

## Development workflow

Run commands in the Compose container:

```bash
docker compose run --rm devarops make init
docker compose run --rm devarops make tests
docker compose run --rm devarops make check
docker compose run --rm devarops make format
docker compose run --rm devarops make linter
docker compose run --rm devarops make coverage
docker compose run --rm devarops make clean
```

`make init` runs clean, editable install, then pytest.

For a persistent container:

```bash
docker compose build devarops
docker compose run -d --name harness_ci devarops sleep infinity
docker exec harness_ci make init
docker exec harness_ci harness version
```

Run a single test file:

```bash
docker compose run --rm devarops pytest tests/test_harness.py --verbose
```

## Project structure

```
harness/
├── harness/
│   ├── __init__.py
│   └── cli.py
├── src/
├── tests/
├── examples/
├── schemas/
├── Makefile
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Key conventions

- The Docker image tracks `python:latest`; `pyproject.toml` declares `>=3.9`.
- flit packaging with `module = "harness"`; `make install` installs it editable and exposes the `harness` console script.
- Typer collapses an app with a single command; the empty callback in `cli.py` keeps `version` dispatchable as `harness version`.
- Version is `0.1.0` in `harness/__init__.py`.
- qed belongs to the consuming repository, not this development image.
- Docstrings follow Google style.
