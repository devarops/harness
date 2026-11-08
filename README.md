# harness

Automated test-driven development for projects that describe their behaviour as
acceptance criteria.

## What it does

Harness takes a project's acceptance criteria and works through them one at a
time. It writes a failing test for the next piece of behaviour, makes the
smallest change that passes it, and then tidies the code, committing after each
step so the history carries the reasoning. Harness keeps no task list of its
own: the specification and the git history are the state.

Today only the first step exists: `harness tdd` checks that the project has a
specification and refuses to run otherwise. The development loop is next.

## Usage

From the root of the project you are developing:

```bash
harness tdd
```

Harness runs on the host and drives Docker behind the scenes; you do not enter
the project's development container yourself.

## Before you start

- Docker and `pi` are installed on the host.
- `harness` is installed on the host.
- The project has one specification under `specs/`, acceptance tests through
  its public interface, a clean working tree, and a running development
  container with qed and the test commands.
- The prompts are in `~/.config/opencode/commands/`.

## Run the project

Install the command with pipx and check it:

```bash
pipx install --editable .
harness version
```

`AGENTS.md` has the workflow for developing harness itself.
