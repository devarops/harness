# harness


Repository for **harness**, a tool for automated TDD cycles driven by specifications.

## Public interface

The public interface is the `harness` Typer CLI.

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
