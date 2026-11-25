# Plan: harness as an ATDD/TDD orchestrator for qed repositories

Status: agreed design for the Python implementation. The prompts in `~/.config/opencode/commands/` are fixed; harness adapts to them.

## What harness is

Harness develops application repositories that follow the qed acceptance standard. It is not an application repository:

- Harness does not carry `specs/*.spec.toml`.
- Harness does not follow the qed standard itself.
- The standard describes harness's input.
- Harness's own tests remain ordinary Python tests.

Harness runs on the host, invokes `pi` prompts in separate sessions, and commits the activation that `atdd-acceptance` leaves uncommitted. The specs and the git history are the state; harness keeps no task state.

## The input contract

A conforming target repository provides:

- One or more top-level `specs/*.spec.toml`, owned by humans.
- An `AGENTS.md` with a public-interface heading or label that declares one interface.
- Acceptance tests written through that interface.
- A running development container named `<repo>_dev` with qed and the test tools, where `make verify`, `make tests`, and `make mutants` run. `make mutants` exits zero only when no mutant survives.
- The prompt files in `~/.config/opencode/commands/`, used unchanged; `afk-mutant-kill` and `afk-mutant-commit` serve the mutation loop.
- Tests under `tests/` (pytest or testthat) or `spec/` (ShellSpec), and fixtures under `tests/data/`; everything outside those paths is production, except `specs/` and `AGENTS.md`.
- A clean working tree, and a `.gitignore` that ignores `harness.log` and the two refactor count files.

Harness requires `pi` on the host and `qed` in the development container.

## Public interface

```text
harness tdd [--max-passes N] [--model MODEL]
```

`harness tdd` runs the loop against the repository in the current directory. A pass is one outer-loop iteration: one `atdd-acceptance` run plus its route. The default pass limit is 10; exhausting it exits nonzero.

The same input sizes the refactor and hunting loops inside each inner cycle. Each loop counts its attempts separately and resets them for every cycle. `--model` is optional: when omitted, `pi` uses its configured model; when given, harness passes `--models` to `pi`.

A later `harness refactor` command is out of scope; it follows the same CLI pattern and needs its own design.

## The two loops

Harness runs the ATDD outer loop and the TDD inner loop. The outer loop decides what to build; the inner loop builds it one failing unit test at a time.

Before the first pass, a startup gate runs `make verify` once. A failure aborts the run; a pass starts the outer loop. The static preflight runs before the gate, and the only other verification runs at the end of the inner loop.

### Outer loop

1. `atdd-acceptance` runs in a fresh `pi` session. It emits `<promise>COMPLETE</promise>` when no criterion remains skipped, and that marker ends the run successfully. Otherwise it removes one `skip` line from one `specs/*.spec.toml`, activating that criterion.
2. Harness captures qed, refuses more than one failing unskipped criterion, commits the removed line, and runs `atdd-red`. It refuses a red commit that adds production.
3. After `atdd-red`, the inner loop runs. The inner loop returns to acceptance only when its verification passes.

### Inner loop

One inner cycle runs three prompts, then the hunting loop, then the scored refactor loop:

1. `afk-red` leaves one failing unit test uncommitted; harness refuses production changes.
2. `afk-fail` commits the test; harness refuses a commit that adds production.
3. `afk-green` commits the production change; harness refuses a commit that adds a test.

After `afk-green`, harness hunts mutants:

- It runs `make mutants` in the container. A zero exit goes to the refactor loop.
- With survivors, `afk-mutant-kill` runs `make mutants` itself, kills one survivor by adding a test, and leaves the test uncommitted. Harness requires the working tree to change, and only under `tests/`.
- `afk-mutant-commit` validates `make tests` and commits the test. Harness requires the new commit to touch only `tests/`.
- The loop repeats until `make mutants` exits zero. It stops after the pass limit and aborts if survivors remain.
- The log line is `--- Mutant hunting N of M ---`; the commit prompt has no line of its own.

After the hunting loop, harness runs the scored refactor loop:

- `afk-refactor` runs. A run that commits nothing ends the loop.
- The touched files are the paths from the pre-refactor commit to the new one.
- Harness clears the before and after count files and scores both commits three times each, with the commit and the file list appended to the prompt text. Each run prints `<score>N</score>`; harness keeps the valid integers and appends them to the version's count file.
- Each version's count is the median of its file.
- A lower after median keeps the refactor and starts another attempt. An equal median keeps it and ends the loop. A higher median resets one commit, checks that the tree is clean, and ends the loop. No valid score keeps the refactor and ends the loop.
- The loop also ends at the pass limit, keeping the last improvement.

After the refactor loop, harness runs `make tests`; a failure aborts. It then runs `make verify`; a failure repeats the inner cycle, and a pass returns to acceptance.

An inner cycle starts after `atdd-red` or after a failing verification at its end. It ends only when verification passes, so acceptance never sees a failing active criterion.

## Routing

Harness captures `docker exec <repo>_dev qed verify specs --json` and maps the report onto the specs:

- qed names each spec and lists its criteria in TOML order. Harness maps specs by `name` and pairs criteria by index after checking that the counts and descriptions agree.
- Duplicate names, names qed reports without a top-level file, and criteria counts that disagree abort the run.
- More than one failing unskipped criterion aborts the run and names them, because `atdd-red` validates a single new failure.
- Exit code 1 is a verification result; exit code 2 aborts.

After each capture, a spec is open when any of its criteria is skipped or failed. Several specs may be open, and the acceptance prompt activates one skip from them by dependency and risk.

## Commit responsibilities

| Phase | Durable effect | Harness check |
| --- | --- | --- |
| `atdd-acceptance` | one `skip` removal in one spec | one changed spec path with one removed skip line; harness commits it |
| `atdd-red` | zero or one commit: acceptance test and fixtures | the commit adds no production |
| `afk-red` | an uncommitted unit test and fixtures | the working tree changes no production |
| `afk-fail` | one commit: the unit test and fixtures | the commit adds no production |
| `afk-green` | one commit: production | the last commit adds no test |
| `afk-mutant-kill` | an uncommitted test under `tests/` | the working tree changes, and only under `tests/` |
| `afk-mutant-commit` | one commit: tests | the new commit touches only `tests/` |
| `afk-refactor` | zero or one commit: production and tests | the commit adds no fixture; a higher score resets it |
| `afk-score` | no commit; the counts append to a count file | the prompt prints a `<score>` marker |

Tests are paths under `tests/` or `spec/`; fixtures are paths under `tests/data/`, which take precedence over the test path; everything else is production. `specs/` and `AGENTS.md` are always protected.

The harness commits the activation before it runs the acceptance red. It takes the criterion from the diff, not from the prose. The subject uses the criterion's first sentence, normalized to one line and kept under 72 characters; the body is the captured activation report.

## State and artifacts

- Harness keeps no task state.
- It captures qed JSON in memory for the capture; no transient file is written.
- `harness.log` at the target root is the run log. The target `.gitignore` must ignore it, and preflight aborts otherwise. Harness appends to it.
- The refactor loop writes two count files at the target root, before and after. The target `.gitignore` must ignore them like `harness.log`; harness clears them for each attempt.
- The mutation tools' caches stay out of the tree; a `make mutants` run leaves the working tree clean.
- The specs' `skip` fields are the only durable scheduler state.
- Git history is the task history. The prompts write commit messages that carry context between sessions.

Every prompt appends one deterministic line and then its output to `harness.log`, except the score runs, which write to the count files and add the two medians, and the mutation commit prompt, which has no line. The lines are `=== Acceptance cycle 4 of 10 ===`, `=== ATDD Red ===`, `--- TDD cycle 2 (ATDD 4/10) ---`, `--- TDD Red ---`, `--- TDD Fail ---`, `--- TDD Green ---`, `--- Refactor 3 of 10 ---`, and `--- Mutant hunting 2 of 10 ---`. A counter line announces each change of its counter and also serves as that prompt's line. The style follows the loop: heavy for ATDD and light for TDD.

## Protected input

- Harness never edits the specs except the `skip` field that `atdd-acceptance` removes.
- Harness never edits `AGENTS.md`.
- Harness never edits acceptance tests; `atdd-red` owns their creation, and `afk-refactor` may refactor test code.
- After an activation, harness checks that one spec changed and that exactly one `skip` line left.

## Prompt contract

The prompts live in `~/.config/opencode/commands/` and are read at runtime:

- `atdd-acceptance.md`
- `atdd-red.md`
- `afk-red.md`
- `afk-fail.md`
- `afk-green.md`
- `afk-refactor.md`
- `afk-score.md`
- `afk-mutant-kill.md`
- `afk-mutant-commit.md`

The prompts are used unchanged. Harness invokes `pi [--models MODEL] --no-session --print` for each prompt. The score prompt receives the commit and the file list appended to its text. The prompts do not share a session. Commit messages carry the context. Harness aborts on an `<error>FAIL` marker or a non-zero `pi` exit, detects the `<promise>COMPLETE</promise>` marker, and extracts `<score>N</score>` from the score prompt. The prompts' reports stay prose: harness uses them as log and commit bodies, never for routing, except the score marker that the refactor loop reads.

## Python modules

`harness/cli.py` parses options and calls `harness/tdd.py`. The primary module imports the shared modules; `cli.py` does not.

- `tdd.py`: the loop, the gates, the path checks, preflight, the pass limit, the hunting loop, and the scored refactor loop.
- `prompts.py`: run a prompt, capture output, detect the failure and completion markers.
- `scoring.py`: run `afk-score`, extract the `<score>` marker, keep the valid runs, write the count files, and compare the medians.
- `docker.py`: run commands in `<repo>_dev`.
- `qed.py`: run `qed verify specs --json`, parse it, and map specs by name and criteria by index.
- `spec.py`: read the top-level TOML specs and their criteria; reject duplicate names and malformed criteria.
- `git.py`: clean tree, status, working-tree and commit diffs, commits, reset, and HEAD.
- `commit.py`: build the activation message.
- `log.py`: append to `harness.log`.

## Preflight

Before the first pass, harness checks:

- At least one top-level `specs/*.spec.toml` exists.
- `AGENTS.md` declares the public interface.
- The target `.gitignore` names `harness.log` and the two count files.
- The score and mutation prompt files exist.
- `make -n mutants` succeeds in the container.
- The working tree is clean.

The container is inspected when a command first runs, and `pi` is required on the host.

## Why not `qed run`

qed's worker loop already runs a worker, verifies, and feeds failures back. Harness adds what qed does not:

- the ATDD outer loop and the TDD inner loop;
- the acceptance-test red that precedes the unit cycle;
- the mutation loop after the green commit;
- commit granularity per phase;
- context transfer through commit messages;
- the harness-owned activation commit;
- repository-level preflight and logging.

That structure is harness's reason to exist.

## Tests

`tests/test_cli.py` covers the public CLI, including `--max-passes` and `--model`. `tests/test_spec.py` covers spec discovery, duplicate names, criteria parsing, and the rejection of malformed criteria. The remaining unit tests cover:

- the capture: the single-failure limit;
- qed JSON parsing, name mapping, and criteria-count checks;
- prompt invocation and the failure and completion markers;
- git status, working-tree and commit diffs, commits, reset, and activation commits;
- the path checks for each phase;
- the startup gate, and the inner loop's tests and verification gates, including its repeat until verification passes;
- the score protocol: `<score>` extraction, invalid runs, the count files, and the median;
- the scored refactor loop: the four median outcomes and the pass limit;
- the hunting loop: no survivors, a survivor, the tests-only paths, the commit check, and the pass limit;
- the preflight for the score and mutation prompts, the count files, and the mutants target;
- the log lines.

Loop tests use a fake `pi` and a fake development container. They do not require Docker. Loop tests assert which prompts ran and in what order, and the counts only where the count is the behavior under test.
