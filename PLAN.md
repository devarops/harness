# Plan: harness as an ATDD/TDD orchestrator for qed repositories

Status: agreed design for the Python implementation. The bash prototype in `src/` is the behavioral reference and will be retired.

## What harness is

Harness develops application repositories that follow the qed acceptance standard. It is not an application repository:

- Harness does not carry `specs/*.spec.toml`.
- Harness does not follow the qed standard itself.
- The standard describes harness's input.
- Harness's own tests remain ordinary Python tests.

Harness runs on the host, invokes `pi` prompts in separate sessions, and commits the activation that `atdd-acceptance` leaves uncommitted. The specs and the git history are the state; harness keeps no task state.

## The input contract

A conforming target repository provides:

- One or more top-level `specs/*.spec.toml`, owned by humans; at most one may have skipped or failing criteria.
- An `AGENTS.md` that declares exactly one public interface.
- Acceptance tests written through that interface.
- A running development container named `<repo>_dev` with qed, `make verify`, `make tests`, and the test tools.
- The prompt files in `~/.config/opencode/commands/`.
- A clean working tree.

Harness requires `pi` on the host and `qed` in the development container.

## Public interface

```text
harness tdd [--max-passes N]
```

`harness tdd` runs the loop against the repository in the current directory. The default pass limit is 10. Later commands (`harness refactor`, `harness html`) follow the same CLI pattern.

## The two loops

Harness runs the ATDD outer loop and the TDD inner loop. The outer loop decides what to build; the inner loop builds it one failing unit test at a time.

### Outer loop

1. `atdd-acceptance` runs in a fresh `pi` session.
   - It reports the first failing unskipped criterion.
   - It activates one skipped criterion when every active criterion passes and skipped criteria remain.
   - It emits `<promise>COMPLETE</promise>` when no criterion remains skipped.
   - It emits `<error>FAIL</error>` only for misconfiguration.
2. If the report is `COMPLETE`, or the capture shows no open spec, harness stops successfully.
3. If `atdd-acceptance` activated a criterion, it leaves the `skip` removal uncommitted. Harness commits that edit and then routes the activated criterion.
4. Harness routes the selected criterion:
   - Missing acceptance test: run `atdd-red`.
   - Existing acceptance test: run the inner loop.
5. After `atdd-red` or one inner cycle, harness returns to `atdd-acceptance`.

### Inner loop

One inner cycle runs four prompts in order:

1. `afk-red` writes and validates one failing unit test and leaves it uncommitted.
2. `afk-fail` re-validates the test and commits it.
3. `afk-green` implements the smallest production change and commits it.
4. `afk-refactor` applies one safe refactoring and commits it.

Harness runs one cycle and returns to the outer loop. The acceptance check decides whether another cycle is needed.

## Routing

Harness does not parse the prompt prose to route. It captures `qed verify --json` from `<repo>_dev` and reads the open spec:

- The first failing unskipped criterion in the open spec is the routing target.
- The verify command names the acceptance test. Harness checks whether that file and node, or file and group, exist.
- A missing test routes to `atdd-red`; an existing test routes to the inner loop.

The acceptance and Red prompts run their own `make verify`; the Green and Refactor prompts run `make tests`. The duplication is intentional: the prompts need the failure text, and harness needs structured JSON for routing.

### Several specs

Harness reads only the top-level `specs/*.spec.toml`; it does not recurse into subdirectories. It maps the specs in the qed JSON to their TOML files by the `name` field. Duplicate names, and names qed reports without a top-level file, abort the run.

After each capture, a spec is open when any of its criteria is skipped or failed. At most one spec may be open; two or more abort the run and name them. Zero open specs end the run successfully, even when the acceptance prompt has not reported completion.

The open spec is the spec in play: routing reads its criteria, and the acceptance prompt activates its skips.

## Commit responsibilities

| Step | Leaves uncommitted | Harness action |
| --- | --- | --- |
| `atdd-acceptance` | one `skip` removal | commit it |
| `atdd-red` | nothing | verify the tree is clean |
| `afk-red` | the new unit test | verify the expected files |
| `afk-fail` | nothing | verify the tree is clean |
| `afk-green` | nothing | verify the tree is clean |
| `afk-refactor` | nothing | verify the tree is clean |

The harness commits the activation before it runs `atdd-red`. It names the criterion in the subject and uses the activation report as the body:

```text
🔧 Activate the <criterion> acceptance criterion

<the atdd-acceptance activation report, including the dependency and risk rationale>
```

## State and artifacts

- Harness keeps no task state.
- It captures qed JSON in memory for routing. A transient copy may be written for debugging, but it is not state and is ignored by Git.
- `harness.log` at the target root is the run log.
- The specs' `skip` fields are the only durable scheduler state.
- Git history is the task history. The prompts write commit messages that carry context between sessions.

## Protected input

- Harness never edits the specs except the `skip` field that `atdd-acceptance` removes.
- Harness never edits acceptance tests; `atdd-red` owns them.
- After an activation, harness checks that the spec diff contains only the removed `skip` line. Any other spec change aborts the run.
- Harness aborts when a prompt changes a protected path unexpectedly.

## Prompt contract

The prompts live in `~/.config/opencode/commands/` and are read at runtime:

- `atdd-acceptance.md`
- `atdd-red.md`
- `afk-red.md`
- `afk-fail.md`
- `afk-green.md`
- `afk-refactor.md`

Harness invokes `pi --no-session --print` for each prompt. The prompts do not share a session. Commit messages carry the context. Harness aborts on `<error>FAIL</error>` or a non-zero `pi` exit.

## Python modules

`harness/cli.py` parses options and calls `harness/tdd.py`. The primary module imports the shared modules; `cli.py` does not.

- `tdd.py`: the loop, routing, and pass limit.
- `prompts.py`: run a prompt, capture output, detect `<error>FAIL</error>` and `<promise>COMPLETE</promise>`.
- `docker.py`: run commands in `<repo>_dev`.
- `qed.py`: run and parse `qed verify --json`.
- `spec.py`: read the top-level TOML specs and their criteria; reject duplicate names; check acceptance test existence.
- `git.py`: clean tree, status, commits, and HEAD.
- `commit.py`: build the activation message.
- `log.py`: append to `harness.log`.

## Preflight

Before the first pass, harness checks:

- It runs at the target repository root.
- The working tree is clean.
- At least one top-level `specs/*.spec.toml` exists, with unique names.
- `AGENTS.md` declares exactly one public interface.
- `<repo>_dev` is running and has qed.
- `make verify` and `make tests` targets exist.
- `pi` is on the host.
- All six prompt files exist.

## Why not `qed run`

qed's worker loop already runs a worker, verifies, and feeds failures back. Harness adds what qed does not:

- the ATDD outer loop and the TDD inner loop;
- the missing-test versus missing-behavior route;
- commit granularity per phase;
- context transfer through commit messages;
- the harness-owned activation commit;
- repository-level preflight and logging.

That structure is harness's reason to exist.

## Tests

`tests/test_cli.py` covers the public CLI, and `tests/test_spec.py` covers spec discovery. The remaining unit tests cover:

- spec parsing and test existence;
- the open-spec invariant: zero, one, and several open specs;
- qed JSON parsing;
- prompt output parsing;
- git status and activation commits;
- routing from a failing criterion to `atdd-red` or the inner loop.

Loop tests use a fake `pi` and a fake development container. They do not require Docker.

## Prototype retirement

- `src/tdd.sh`, `src/refactor.sh`, and `src/acceptance-to-html.sh` are the behavioral reference.
- Remove them once the Python modules replace them.
- Remove `schemas/acceptance.schema.json` and `examples/acceptance.json`; `acceptance.json` is no longer task state.
- `afk-gold` is gone; `atdd-acceptance` replaces it.
- Future commands: `harness refactor` from `src/refactor.sh`; `harness html` from `src/acceptance-to-html.sh`.
