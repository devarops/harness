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
- A running development container named `<repo>_dev` with qed and the test tools, where `make verify` runs the acceptance suite, `make tests` runs the unit suite, and `make mutants` runs the mutation tool and its results command. `make mutants` exits zero when the run completed, with or without survivors, and nonzero only when the run could not start. It honors an optional `ACTIVE` make variable by deselecting that pytest node.
- The target's test command ignores the mutation tool's working copy, such as `pytest --ignore=mutants`.
- The prompt files in `~/.config/opencode/commands/`, used unchanged.
- Tests under `tests/` (pytest or testthat) or `spec/` (ShellSpec), and fixtures under `tests/data/`; everything outside those paths is production, except `specs/` and `AGENTS.md`.
- A clean working tree, and a `.gitignore` that ignores `harness.log` and the two refactor count files.

Harness requires `pi` on the host and `qed` in the development container.

## Public interface

```text
harness tdd [--max-passes N] [--model MODEL]
```

`harness tdd` runs the loop against the repository in the current directory. A pass is one outer-loop iteration: one `atdd-acceptance` run plus its route. The default pass limit is 10; exhausting it prints a DONE line and exits nonzero.

The same input sizes the refactor loop and, across the run, the survivor streak. The streak counts consecutive unit cycles that the mutation suite rejected; a clean run resets it. The refactor loop resets its attempts for every cycle. `--model` is optional: when omitted, `pi` uses its configured model; when given, harness passes `--models` to `pi`.

Two later commands are planned, and neither is designed yet. Both follow the same CLI pattern and call one primary module.

- `harness mutate` hunts all the mutants, one by one, in an automated loop.
- `harness refactor` runs the scored refactor loop on the current tree.

## The two loops

Harness runs the ATDD outer loop and the TDD inner loop. The outer loop decides what to build; the inner loop builds it one failing unit test at a time.

Before the first pass, a startup gate runs `make verify` once. A failure aborts the run; a pass starts the outer loop. The static preflight runs before the gate. After that, the only full make verify runs at the start of each inner iteration; the mutation gate runs one criterion's verify command.

### Outer loop

1. `atdd-acceptance` runs in a fresh `pi` session. It emits `<promise>COMPLETE</promise>` when no criterion remains skipped, and that marker ends the run successfully. Otherwise it removes one `skip` line from one `specs/*.spec.toml`, activating that criterion.
2. Harness captures qed, refuses more than one failing unskipped criterion, and commits the removed line. If the activated criterion passes, acceptance runs again. If it fails, harness runs `atdd-red` and refuses a red commit that adds production.
3. After `atdd-red`, the inner loop runs. It verifies before any unit prompt; a pass returns to acceptance, and a failure starts a unit cycle.

### Inner loop

One inner cycle runs three prompts, then the mutation gate, then, only after a clean gate, the scored refactor loop:

1. `afk-red` leaves one failing unit test uncommitted; harness refuses production changes.
2. `afk-fail` commits the test; harness refuses a commit that adds production.
3. `afk-green` commits the production change; harness refuses a commit that adds a test.

After `afk-green`, harness runs the mutation gate:

- It records HEAD before `afk-red` as the cycle base, so the reset restores the state the cycle started from.
- It runs the activated criterion's verify command. If the test fails, it is still red and cannot judge mutants, so harness passes its pytest node as `ACTIVE`. If it passes, harness passes no exclusion.
- It runs `make mutants` in the container. A nonzero exit aborts the run, because the mutation suite could not start.
- It reads the `mutmut results` lines that `make mutants` prints and counts the mutants marked survived. Timeouts do not count.
- A clean run resets the streak to zero and starts the refactor loop.
- With survivors, harness announces the streak, runs a hard reset to the cycle base, and cleans the tree. The `afk-fail` and `afk-green` commits disappear; the activation and the acceptance test stay. The reset removes whatever those two steps committed, including when a step committed nothing.
- After the reset, the criterion is red again, so harness runs `make mutants` with its node excluded. A nonzero exit or a surviving mutant aborts the run, because the undo did not restore a clean baseline.
- A clean recheck increments the streak. At the limit the run stops with an error. Otherwise the next cycle starts at `afk-red`, without a verify, because the reset restored a state where the criterion already failed.
- The exclusion is pytest-only. An active verify command that is not a pytest node aborts the run with an unsupported-exclusion error.

A clean gate starts the scored refactor loop:

- `afk-refactor` runs. A run that commits nothing ends the loop.
- The touched files are the paths from the pre-refactor commit to the new one.
- Harness clears the before and after count files and scores both commits three times each, with the commit and the file list appended to the prompt text. Each run prints `<score>N</score>`; harness keeps the valid integers and appends them to the version's count file.
- Each version's count is the median of its file.
- A lower after median keeps the refactor and starts another attempt. An equal median keeps it and ends the loop. A higher median resets one commit, checks that the tree is clean, and ends the loop. No valid score keeps the refactor and ends the loop.
- The loop also ends at the pass limit, keeping the last improvement.

After the refactor loop, harness runs `make tests`; a failure aborts. The next iteration verifies: a pass returns to acceptance, and a failure runs another cycle.

The first verification follows `atdd-red`, so a criterion the red satisfied returns without a unit cycle. An inner cycle starts when the verification at the start of an inner iteration fails, and the loop ends when that verification passes, so acceptance never sees a failing active criterion. A rejected cycle restarts at `afk-red`, because its reset restores the state where the criterion failed.

## Routing

Harness captures `docker exec <repo>_dev qed verify specs --json` and maps the report onto the specs:

- qed names each spec and lists its criteria in TOML order. Harness maps specs by `name` and pairs criteria by index after checking that the counts and descriptions agree.
- Duplicate names, names qed reports without a top-level file, and criteria counts that disagree abort the run.
- More than one failing unskipped criterion aborts the run and names them, because `atdd-red` validates a single new failure.
- The activated criterion is the one whose skip left. Harness reads its result from the capture: a pass returns to acceptance, and a failure runs `atdd-red`.
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
| `afk-refactor` | zero or one commit: production and tests | the commit adds no fixture; a higher score resets it |
| `afk-score` | no commit; the counts append to a count file | the prompt prints a `<score>` marker |

The mutation gate owns no prompt and no commit. On survivors it resets to the cycle base and cleans the tree, so the rejected cycle leaves no trace.

Tests are paths under `tests/` or `spec/`; fixtures are paths under `tests/data/`, which take precedence over the test path; everything else is production. `specs/` and `AGENTS.md` are always protected.

The harness commits the activation before it runs the acceptance red. It takes the criterion from the diff, not from the prose. The subject uses the criterion's first sentence, normalized to one line and kept under 72 characters; the body is the captured activation report.

## State and artifacts

- Harness keeps no task state.
- It captures qed JSON in memory for the capture; no transient file is written.
- The survivor streak lives in memory for the run; a new run starts it at zero.
- `harness.log` at the target root is the run log. The target `.gitignore` must ignore it, and preflight aborts otherwise. Harness appends to it.
- The refactor loop writes two count files at the target root, before and after. The target `.gitignore` must ignore them like `harness.log`; harness clears them for each attempt.
- The mutation tool's caches stay out of the tree; the target's test command ignores its working copy, a `make mutants` run leaves the working tree clean, and the gate's clean leaves the ignored log and count files.
- The specs' `skip` fields are the only durable scheduler state.
- Git history is the task history. The prompts write commit messages that carry context between sessions.

Every prompt appends one deterministic line and then its output to `harness.log`, except the score runs, which write to the count files and add the two median lines. Every line prints and is logged. The lines are `=== Acceptance cycle 4 of 10 ===`, `=== ATDD Red ===`, `--- TDD cycle 2 (ATDD 4/10) ---`, `--- TDD Red ---`, `--- TDD Fail ---`, `--- TDD Green ---`, `--- TDD Refactor 3 of 10 ---`, `--- TDD Mutants survived 2 of 10 ---`, `--- TDD Median weakness count before 4 ---`, and `--- TDD Median weakness count after 2 ---`. A counter line announces each change of its counter and also serves as that prompt's line. The style follows the loop: heavy for ATDD and light for TDD.

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

The prompts are used unchanged. Harness invokes `pi [--models MODEL] --no-session --print` for each prompt. The score prompt receives the commit and the file list appended to its text. The prompts do not share a session. Commit messages carry the context. Harness aborts on an `<error>FAIL` marker or a non-zero `pi` exit, detects the `<promise>COMPLETE</promise>` marker, and extracts `<score>N</score>` from the score prompt. The prompts' reports stay prose: harness uses them as log and commit bodies, never for routing, except the score marker that the refactor loop reads.

## Python modules

`harness/cli.py` parses options and calls `harness/tdd.py`. The primary module imports the shared modules; `cli.py` does not.

- `tdd.py`: the loop, the gates, the path checks, preflight, the pass limit, the mutation gate, and the scored refactor loop.
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
- The score prompt file exists.
- `make --dry-run mutants` succeeds in the container, and then `make mutants` exits zero and reports no surviving mutant in its results.
- The working tree is clean.

The container is inspected when a command first runs, and `pi` is required on the host.

## Why not `qed run`

qed's worker loop already runs a worker, verifies, and feeds failures back. Harness adds what qed does not:

- the ATDD outer loop and the TDD inner loop;
- the acceptance-test red that precedes the unit cycle;
- the mutation gate after the green commit;
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
- the startup gate, the post-activation criterion check, the first inner verification, the cycle's tests gate, and the repeat until verification passes;
- the score protocol: `<score>` extraction, invalid runs, the count files, and the median;
- the scored refactor loop: the four median outcomes and the pass limit;
- the mutation gate: the active test check and its exclusion, the results parsing, timeouts ignored, a run that cannot start, a clean run, a survivor reset, the recheck, and the streak limit;
- the preflight for the mutants dry run and real run, the score prompt, and the count files;
- the log lines.

Loop tests use a fake `pi` and a fake development container. They do not require Docker. Loop tests assert which prompts ran and in what order, and the counts only where the count is the behavior under test.
