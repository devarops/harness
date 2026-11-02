# Plan: harness as a TDD orchestrator for qed repositories

Status: agreed design; the `harness tdd` command is not implemented yet.

## What harness is

Harness is tooling that develops application repositories which follow the qed
acceptance standard. Harness is not an application repository:

- Harness does not carry `specs/*.spec.toml`.
- Harness does not follow the qed standard itself.
- The standard describes harness's input.
- Harness's own tests remain ordinary Python tests.

## The input contract

A conforming application repository provides:

- `specs/*.spec.toml`, owned by humans.
- Human-written acceptance tests, following the standard's naming convention.
- A running development container named `<repo>_dev`, containing qed and the
  testing and development tools.
- `make tests`, which the `afk-*` prompts run as
  `docker exec <repo>_dev make tests`.

Harness itself requires only qed verification. The prompts rely on `make tests`
for the inner TDD loop.

## Public interface

The only new public command in this plan is:

```text
harness tdd
```

It runs the TDD loop against the repository in the current directory.

## One pass

A pass is one full iteration, bounded by a global maximum (default 10):

1. `pi` runs `afk-red`: it selects the first failing criterion in spec file
   order, ignoring `skip`, and writes one failing unit test.
2. `pi` runs `afk-green`: it implements the smallest change that passes the
   test.
3. `pi` runs `afk-refactor`: it applies one safe refactoring.
4. Harness refreshes `acceptance.json` by running qed.
5. `pi` runs `afk-acceptance`: it reads `acceptance.json` and reports status.

Harness then parses `acceptance.json` and decides whether to stop or start
another pass.

## Control rules

- Selection belongs to `afk-red`, following its rule at `afk-red.md:13`.
  Harness does not select criteria.
- Judgment belongs to harness: it parses `acceptance.json` to decide success,
  continuation, and failure.
- Success: every criterion passes. Harness exits successfully.
- Failure: the global pass limit is reached. Harness exits unsuccessfully.
- There is no per-criterion retry cap.
- There is no durable task state. Only `harness.log` and the transient
  `acceptance.json` exist.
- Any phase failure aborts: `<error>FAIL</error>` or a non-zero `pi` exit stops
  the run.
- A dirty tree after a phase aborts and reports `git status`.
- `afk-acceptance` treats failing criteria as data, not as a phase failure. It
  reports them and exits 0. It emits `<error>FAIL</error>` only when it cannot
  read or parse `acceptance.json`.

## Execution and artifacts

Harness runs on the host. It captures qed's JSON output with:

```text
docker exec <repo>_dev qed verify --json specs > acceptance.json
```

`qed verify --json` writes JSON to stdout; qed does not write a file by itself.
Harness creates `acceptance.json` at the repository root and adds it to
`.git/info/exclude`. The file is transient output, not task state.

`harness.log` at the repository root is the run log. It is ignored by Git.

## Protected input

Harness records `HEAD` at the start of each pass and checks protected paths
across `baseline..HEAD` plus the working tree:

- `specs/**`
- Acceptance tests following the standard's naming convention, such as
  `tests/test_acceptance_*` and `test-acceptance-*`

If anything protected changed, harness aborts the run and reports the diff. It
does not revert or rewrite history.

## Prompt contract

The four prompts live in `~/.config/opencode/commands/` and are read at runtime:

- `afk-red.md`
- `afk-green.md`
- `afk-refactor.md`
- `afk-acceptance.md`

The plan includes updating the dotfiles copies so that:

- `afk-red`, `afk-green`, and `afk-refactor` do not run qed.
- `afk-red` selects from `acceptance.json`.
- `afk-acceptance` only reads `acceptance.json`.
- Only harness runs `qed verify --json`.

Harness invokes `pi` directly, as `src/tdd.sh` does.

## Preflight

Before the first pass, harness validates:

- it runs from the repository root;
- the working tree is clean;
- `specs/` exists;
- `<repo>_dev` is running;
- qed is available there;
- `pi` is available on the host;
- all four prompt files exist.

## Why not `qed run`

qed's worker loop already runs a worker, verifies, feeds failures back, and
guarantees termination. Harness adds what qed does not:

- red, green, and refactor discipline;
- one criterion at a time through `afk-red`;
- commit granularity per phase;
- a guard for human-owned specs and acceptance tests;
- repository-level preflight and logging.

That TDD structure is harness's reason to exist.

## Tests

`tests/test_cli.py` is the high-level suite for the public interface. It covers:

- `harness version` through `CliRunner`;
- the installed `harness` console script;
- `harness tdd --help`;
- `harness tdd` refusing a directory without `specs/`.

The last two tests are red until `harness tdd` exists.

## Cleanup in the harness repository

- Approval was a dead golden-master experiment: `approval/` and
  `tests/approval/` are removed.
- The harness CLI suite moved from `acceptance/test_cli.py` to
  `tests/test_cli.py`; the `make acceptance` target is removed.
- Acceptance in target repositories remains the live concept.
- Old acceptance-state machinery still to remove:
  `schemas/acceptance.schema.json`, `examples/acceptance.json`,
  `src/acceptance-to-html.sh`, and the acceptance/gold phases in `src/tdd.sh`
  and `src/refactor.sh`.
- The remaining shell prototypes stay as behavioral reference until Python
  modules replace them.
- `acceptance.json` now means only "captured qed JSON", not the old
  task-status file.
