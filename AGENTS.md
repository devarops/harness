# harness


Repository for **harness**, a tool for automated TDD cycles driven by specifications.

## Public interface

The public interface is the `harness` Typer CLI.

## Layering

The Typer CLI is the high-level layer: the outermost entry point. The Python modules are the low-level layer: the implementation the CLI calls.

- A nontrivial command calls exactly one primary module. The planned `tdd` command calls `harness/tdd_loop.py`; the refactor and HTML commands follow the same rule.
- `cli.py` parses options and calls that module. It holds no loop, Docker, prompt, or scoring logic.
- Shared modules are imported by the primary module, never by `cli.py`.
- The primary module exposes one public entry point and may keep private helpers.
- `harness version` is the only command that does not delegate to a module.
- This one-module-per-command rule is stricter than the Typer CLI pattern below.

## Typer CLI pattern

A CLI package follows this pattern:

- Packaging: flit metadata declares the module and depends on `typer`; `[tool.flit.scripts]` maps an explicit console script name to `pkg.cli:<instance>`. The script name may differ from the package name.
- The Typer CLI lives in `pkg/cli.py`: a module-level `typer.Typer()` instance named `cli`.
- Commands are flat `@cli.command()` functions with verb-first names; Typer turns underscores into hyphens.
- Options use `Annotated[type, typer.Option()]`.
- Domain logic lives in modules beside `cli.py`; the CLI imports and calls them, and one command may call more than one module. Domain modules do not import Typer.
- The CLI may hold presentation and configuration; reusable logic stays in the domain modules.
- Options cross as individual arguments, not a shared options object.
- `__init__.py` exposes `__version__` and re-exports domain functions; the CLI may also be re-exported, but the console script targets `pkg.cli`.
- A `version` command prints the package version; it is optional.
- The CLI registers multiple flat commands; a callback is only needed to keep a single-command CLI dispatchable.
- `cli.py` has no `try`/`except`, `sys.exit`, or `typer.Exit`; exceptions propagate, and commands print their command output.
- There is no `__main__.py`; the console script is the invocation.

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
- Typer collapses a single-command CLI; the empty callback in `cli.py` keeps `version` dispatchable as `harness version`.
- qed belongs to the consuming repository, not this development image.
- Docstrings follow Google style.
