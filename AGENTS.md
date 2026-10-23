# harness


Repository for **harness**, a tool for automated TDD cycles driven by specifications.

## Public interface

The public interface is the `harness` Typer CLI.

## Layering

The Typer CLI is the high-level layer: the outermost entry point. The Python modules are the low-level layer: the implementation the CLI calls.

- A nontrivial command calls exactly one primary module. The planned `tdd` command calls `harness/tdd_loop.py`; the refactor and HTML commands follow the same rule.
- `cli.py` parses options and calls that module. It holds no loop, Docker, prompt, or scoring logic.
- Options cross as individual arguments, not a shared options object.
- Shared modules are imported by the primary module, never by `cli.py`.
- The primary module exposes one public entry point and may keep private helpers. It does not import Typer.
- Exceptions propagate; the CLI does not catch them or translate them into exit codes.
- `harness version` is the only exception: it holds its print directly in `cli.py`.
- This one-module-per-command rule is stricter than the IslasGECI pattern, which lets one CLI command call several domain modules.

## Development workflow

Build the image and start the persistent container:

```bash
docker compose build devarops
docker compose run --detach --name harness_ci devarops sleep infinity
docker exec harness_ci make init
```

`make init` runs clean, editable install, then pytest; the suite calls the installed harness command, so it needs that install.

Check the public command:

```bash
docker exec harness_ci harness version
```

Run a single test file:

```bash
docker exec harness_ci pytest tests/test_harness.py --verbose
```

## Key conventions

- The Docker image tracks `python:latest`; `pyproject.toml` declares `>=3.9`.
- flit packaging with `module = "harness"`; `make install` installs it editable and exposes the `harness` console script.
- Typer collapses an app with a single command; the empty callback in `cli.py` keeps `version` dispatchable as `harness version`.
- qed belongs to the consuming repository, not this development image.
- Docstrings follow Google style.
