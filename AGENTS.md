# harness


Repository for **harness**, a tool for automated ATDD/TDD cycles driven by specifications.

## Public interface

The public interface is the `harness` Typer CLI. The only nontrivial command in the current plan is `harness tdd`; it develops a target application repository that follows the qed acceptance standard. See [PLAN.md](PLAN.md).

## Target repositories

Harness is tooling, not an application repository. It does not carry `specs/` and does not follow the qed standard itself. A conforming target repository provides one `specs/*.spec.toml`, an `AGENTS.md` with exactly one public interface, human-written acceptance tests, and a running `<repo>_dev` container with qed and the testing and development tools, where `make verify` and `make tests` run. Harness runs on the host and captures `qed verify --json` from `<repo>_dev` for routing; the prompts run their own `make verify`.

## Layering

The Typer CLI is the high-level layer: the outermost entry point. The Python modules are the low-level layer: the implementation the CLI calls.

- A nontrivial command calls exactly one primary module. The `tdd` command calls `harness/tdd.py`; the later refactor and HTML commands follow the same rule.
- `cli.py` parses options and calls that module. It holds no loop, Docker, prompt, or scoring logic.
- Shared modules are imported by the primary module, never by `cli.py`.
- The primary module exposes one public entry point and may keep private helpers.
- `harness version` is the only command that does not delegate to a module.
- This one-module-per-command rule is stricter than the Typer CLI pattern below.
- For `tdd.py`, the shared modules cover prompts, Docker, qed, specs, git, commits, and logging.

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

Install the CLI and run the suite on the host:

```bash
make init
```

`make init` installs `harness` editable with pipx, then runs pytest. The CLI suite in `tests/test_cli.py` exercises the installed `harness` command, so it needs that install; `pythonpath` in `pyproject.toml` lets the same suite import the package from the checkout.

Run the whole suite:

```bash
make tests
```

Run the CLI suite:

```bash
pytest tests/test_cli.py --verbose
```

Check the public command:

```bash
harness version
```

Run a single test file:

```bash
pytest tests/test_harness.py --verbose
```

## Key conventions

- Harness is developed and tested on the host; `pyproject.toml` declares `>=3.9`.
- flit packaging with `module = "harness"`; `make install` installs it editable with pipx and exposes the `harness` console script.
- Typer collapses a single-command CLI; the empty callback in `cli.py` keeps `version` dispatchable as `harness version`.
- Typer's `CliRunner` does not echo a raised exception, so a command that must report an error prints the message before exiting; `harness/tdd.py` raises `SystemExit(1)`.
- Harness needs Docker on the host, but only for target repositories: it runs `docker exec` against their already-running `<repo>_dev` container.
- `harness tdd` reads six prompts from `~/.config/opencode/commands` and invokes `pi`: `atdd-acceptance`, `atdd-red`, `afk-red`, `afk-fail`, `afk-green`, and `afk-refactor`. Prompts are not bundled with the package.
- Harness keeps no task state: it captures qed JSON in memory and writes `harness.log`. The spec's `skip` field and the git history hold the state.
- The harness commits the `skip` removal that `atdd-acceptance` leaves uncommitted, before it runs `atdd-red`.
- The bash prototype in `src/` is the behavioral reference; remove it once the Python modules replace it.
- qed belongs to the consuming repository's development container, not the host.
- Docstrings follow Google style.
