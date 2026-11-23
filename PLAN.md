# Plan: harness as an ATDD/TDD orchestrator for qed repositories

Status: agreed design for the Python implementation. The prompts in `~/.config/opencode/commands/` are fixed; harness adapts to them. The bash prototypes in `src/` are historical references for the retired `acceptance.json` workflow and are not behavioral references for the qed loop.

## What harness is

Harness develops application repositories that follow the qed acceptance standard. It is not an application repository:

- Harness does not carry `specs/*.spec.toml`.
- Harness does not follow the qed standard itself.
- The standard describes harness's input.
- Harness's own tests remain ordinary Python tests.

Harness runs on the host, invokes `pi` prompts in separate sessions, and commits the activation that `atdd-acceptance` leaves uncommitted. The specs and the git history are the state; harness keeps no task state.

## The input contract

A conforming target repository provides:

- One or more top-level `specs/*.spec.toml`, owned by humans; several may have skipped criteria, but at most one unskipped criterion may fail at a time.
- An `AGENTS.md` with a public-interface heading or label that declares one interface.
- Acceptance tests written through that interface.
- A running development container named `<repo>_dev` with qed, `make verify`, `make tests`, and the test tools.
- The prompt files in `~/.config/opencode/commands/`, used unchanged.
- Tests under `tests/` (pytest or testthat) or `spec/` (ShellSpec), and fixtures under `tests/data/`; everything outside those paths is production, except `specs/` and `AGENTS.md`.
- A clean working tree, and a `.gitignore` that ignores `harness.log`.

Harness requires `pi` on the host and `qed` in the development container.

## Public interface

```text
harness tdd [--max-passes N] [--model MODEL]
```

`harness tdd` runs the loop against the repository in the current directory. A pass is one outer-loop iteration: one `atdd-acceptance` run plus its route. The default pass limit is 10; exhausting it exits nonzero. `atdd-acceptance` runs only when `make verify` passes; while verification fails, the inner cycle repeats until it passes, and those repetitions do not consume the pass limit. The same input sizes the refactor loop inside each inner cycle, which counts its attempts separately and resets them for every cycle. `--model` is optional: when omitted, `pi` uses its configured model; when given, harness passes `--models` to `pi`.

Later commands (`harness refactor`, `harness html`) are out of scope for this plan; they follow the same CLI pattern and need their own design.

## The two loops

Harness runs the ATDD outer loop and the TDD inner loop. The outer loop decides what to build; the inner loop builds it one failing unit test at a time.

### Outer loop

1. Gate. Harness runs `make tests`; a failure aborts the run. Then it runs `make verify`.
   - Passing verification opens the acceptance step.
   - Failing verification opens the inner cycle. More than one failing unskipped criterion aborts the run.
2. `atdd-acceptance` runs in a fresh `pi` session, only from a passing gate.
   - It emits `<promise>COMPLETE</promise>` when no criterion remains skipped, and that marker ends the run successfully.
   - Otherwise it removes exactly one `skip` line from one `specs/*.spec.toml`, activating that criterion. It emits `<error>FAIL` followed by the reason only for misconfiguration.
3. Any change other than a single removed `skip` line in one spec aborts the run, and so does an acceptance run that leaves nothing uncommitted.
4. Harness commits the removed line and captures qed.
   - If the activated criterion passes, the gate repeats.
   - If it fails, harness runs `atdd-red`, which writes the missing acceptance test for that criterion. `atdd-red` reports that the test already exists when it does, and harness aborts on that report.
5. After `atdd-red`, the gate repeats. A passing verification opens acceptance again; a failing one opens another inner cycle.

### Inner loop

One inner cycle runs four prompts in order:

1. `afk-red` writes and validates one failing unit test and leaves it uncommitted.
2. `afk-fail` re-validates the test and commits it.
3. `afk-green` implements the smallest production change and commits it.
4. `afk-refactor` applies one safe refactoring and commits it, or commits nothing when no safe refactoring remains.

After `afk-green`, harness repeats step 4 while each run adds a commit, up to the same limit as the passes, counted separately and reset for each cycle. It compares `HEAD` before and after each run. The loop ends on the first run that adds no commit, and an exhausted budget also ends it without failing the run. A tree left dirty after a run aborts the run.

After the refactor, harness runs `make tests`; a failure aborts the run. It then runs `make verify`. A failing verification repeats the inner cycle from `afk-red`. A passing verification ends the inner cycle and returns to acceptance.

An inner cycle can run before the first acceptance run, when the gate opens with a failing verification. It ends only when verification passes, so acceptance never sees a failing active criterion.

## Routing

Harness does not parse the prompt prose to decide the next step. It captures `docker exec <repo>_dev qed verify specs --json` and reads the activated criterion's result:

- Harness names the criterion from the removed `skip` line and reads its result from the capture.
- qed names each spec and lists its criteria in TOML order. Its JSON does not carry the verify command or a criterion ID, so harness maps specs by `name` and pairs criteria by index after checking that the counts and descriptions agree.
- qed's criterion result is `passed`, `skipped`, or `failed`. Exit code 1 is a verification result, not an execution error; exit code 2 aborts.

The acceptance and Red prompts run their own `make verify`; the Green and Refactor prompts run `make tests`. The duplication is intentional: the prompts need the failure text, and harness needs structured JSON for the capture and its own reads of both commands after the acceptance red.

### Several specs

Harness reads only the top-level `specs/*.spec.toml`; it does not recurse into subdirectories. It maps the specs in the qed JSON to their TOML files by the `name` field. Duplicate names, names qed reports without a top-level file, and criteria counts that disagree abort the run.

After each capture, a spec is open when any of its criteria is skipped or failed. Several specs may be open, and the acceptance prompt activates one skip from them by dependency and risk.

More than one failing unskipped criterion aborts the run and names them, because `atdd-red` validates a single new failure.

## Commit responsibilities

| Phase | Durable effect | Harness check |
| --- | --- | --- |
| `atdd-acceptance` | when it activates, one `skip` removal in one spec | the working tree has one modified spec and exactly one removed line; commit it |
| `atdd-red` | one commit: acceptance test and fixtures | the commit changes tests and `tests/data/` only; no production |
| `afk-red` | uncommitted unit test and fixtures | the working tree changes tests and `tests/data/` only; no production |
| `afk-fail` | one commit: the unit test and fixtures | the commit changes tests and `tests/data/` only; no production |
| `afk-green` | one commit: production | the commit changes production only; no tests and no `tests/data/` |
| `afk-refactor` | zero or one commit: production and tests | the commit changes production and tests only; no `tests/data/` |

Tests are paths under `tests/` or `spec/`; fixtures are paths under `tests/data/`, which take precedence over the test path; everything else is production. `specs/` and `AGENTS.md` are always protected. Red phases abort on any production change. Green aborts on any test change. This is deliberately stricter than the historical target runs, which had a human in the loop.

The harness commits the activation before it runs the acceptance red. It takes the criterion from the diff, not from the prose. The subject uses the criterion's first sentence, normalized to one line and kept under 72 characters; the body is the captured activation report:

```text
🔧 Activate the <criterion> acceptance criterion

<the atdd-acceptance activation report, including the dependency and risk rationale>
```

Harness aborts when a prompt leaves more or fewer changes than its row allows, including any run of `afk-refactor`. A phase may legitimately have nothing to do: `atdd-acceptance` when it reports completion, `atdd-red` when the activated criterion passes, and `afk-refactor` in a run that leaves nothing to refactor. `afk-red` must leave a test uncommitted; `afk-fail` and `afk-green` must add a commit. A clean tree in `afk-red`, a dirty tree after any prompt, or no new commit in `afk-fail` or `afk-green`, aborts.

## State and artifacts

- Harness keeps no task state.
- It captures qed JSON in memory for the capture; no transient file is written.
- `harness.log` at the target root is the run log. The target `.gitignore` must ignore it, and preflight aborts otherwise. Harness appends to it.
- The specs' `skip` fields are the only durable scheduler state.
- Git history is the task history. The prompts write commit messages that carry context between sessions.

Every prompt appends one deterministic line and then its output to `harness.log`. The lines are `=== Acceptance cycle 4 of 10 ===`, `=== ATDD Red ===`, `--- TDD cycle 2 (ATDD 4/10) ---`, `--- TDD Red ---`, `--- TDD Fail ---`, `--- TDD Green ---`, and `--- Refactor 3 of 10 ---`. A counter line announces each change of its counter and also serves as that prompt's line; the prompts under a TDD cycle header keep their own lines. The TDD cycle number counts the inner cycles of its pass, so a repeated inner cycle writes the next number. The style follows the loop: heavy for ATDD and light for TDD.

## Protected input

- Harness never edits the specs except the `skip` field that `atdd-acceptance` removes.
- Harness never edits `AGENTS.md`.
- Harness never edits acceptance tests; `atdd-red` owns their creation, and `afk-refactor` may refactor test code.
- After an activation, harness checks that one spec's diff contains exactly one removed `skip` line. Any other change aborts the run.
- After every prompt, harness enforces the phase allowlist in the commit table. A change outside the phase's allowed paths aborts the run.

## Prompt contract

The prompts live in `~/.config/opencode/commands/` and are read at runtime:

- `atdd-acceptance.md`
- `atdd-red.md`
- `afk-red.md`
- `afk-fail.md`
- `afk-green.md`
- `afk-refactor.md`

The prompts are used unchanged. Harness invokes `pi [--models MODEL] --no-session --print` for each prompt. The prompts do not share a session. Commit messages carry the context. Harness aborts on an `<error>FAIL` marker or a non-zero `pi` exit, and detects the exact `<promise>COMPLETE</promise>` marker. The prompts' reports stay prose: harness uses them as log and commit bodies, never for routing.

## Python modules

`harness/cli.py` parses options and calls `harness/tdd.py`. The primary module imports the shared modules; `cli.py` does not.

- `tdd.py`: the loop, the gates, phase allowlists, preflight, and pass limit.
- `prompts.py`: run a prompt, capture output, detect the `<error>FAIL` prefix and the exact `<promise>COMPLETE</promise>`.
- `docker.py`: run commands in `<repo>_dev`.
- `qed.py`: run `qed verify specs --json`, parse it, and map specs by name and criteria by index.
- `spec.py`: read the top-level TOML specs and their criteria; reject duplicate names and malformed criteria.
- `git.py`: clean tree, status, working-tree and commit diffs, commits, and HEAD.
- `commit.py`: build the activation message.
- `log.py`: append to `harness.log`.

## Preflight

Before the first pass, harness checks:

- It runs at the target repository root.
- The working tree is clean.
- At least one top-level `specs/*.spec.toml` exists, with unique names.
- `AGENTS.md` has a public-interface heading or label. Preflight checks only that the section is present; `atdd-red` decides whether it declares exactly one interface.
- `<repo>_dev` is running and has qed.
- `make verify` and `make tests` targets exist, checked with `make -n` in the container.
- `pi` is on the host.
- All six prompt files exist.
- `harness.log` is ignored by the target `.gitignore` and is not tracked.

## Why not `qed run`

qed's worker loop already runs a worker, verifies, and feeds failures back. Harness adds what qed does not:

- the ATDD outer loop and the TDD inner loop;
- the acceptance-test red that precedes the unit cycle;
- commit granularity per phase;
- context transfer through commit messages;
- the harness-owned activation commit;
- repository-level preflight and logging.

That structure is harness's reason to exist.

## Tests

`tests/test_cli.py` covers the public CLI, including `--max-passes` and `--model`. `tests/test_spec.py` covers spec discovery, duplicate names, criteria parsing, and the rejection of malformed criteria. The remaining unit tests cover:

- the capture: the single-failure limit and the activated criterion's result;
- qed JSON parsing, name mapping, and criteria-count checks;
- prompt invocation and the `<error>FAIL` and `<promise>COMPLETE</promise>` markers;
- git status, working-tree and commit diffs, and activation commits;
- the phase allowlists, including a rejected diff for each phase;
- the gate from `make verify` to acceptance or the inner cycle, and the inner cycle's repeat until verification passes;
- the refactor loop, its budget, and the counted log lines;
- the `harness.log` preflight.

Loop tests use a fake `pi` and a fake development container. They do not require Docker. Loop tests assert which prompt ran and in what order, not how many invocations occurred.

## Prototype retirement

- `src/refactor.sh` and `src/acceptance-to-html.sh` are historical references for the retired `acceptance.json` workflow. They are not behavioral references for the qed loop.
- Remove them once their Python commands replace them.
- `afk-gold` is gone; `atdd-acceptance` replaces it.
- Future commands, out of scope for this plan: `harness refactor` and `harness html` need their own design.
