# Backlog

See `PLAN.md` for the agreed design of the `harness tdd` loop.

The scripts in `src/` are historical references for the retired `acceptance.json` workflow. The qed loop follows the prompts in `~/.config/opencode/commands/` unchanged.

- [x] Implement `prompts.py` — run `pi`, capture its output, and detect the prompt markers.
      Test: a fake `pi` receives the prompt file's text and prints `<promise>COMPLETE</promise>`, `<error>FAIL: reason</error>`, or ordinary prose; the result reports COMPLETE, FAIL with the reason, or neither, and a non-zero `pi` exit aborts; `make tests` passes.
- [x] Implement `docker.py` — run commands in `<repo>_dev`.
      Test: a fake `docker` executable receives the container name, the command, and the working directory, returns stdout and the exit code, and a missing container aborts; `make tests` passes.
- [x] Implement `spec.py` acceptance-test existence — pytest file and node, testthat file and derived group, and ShellSpec file and derived group.
      Test: each runner's present and missing test is detected from a criterion's `verify.run`, and a malformed or unsupported command aborts; `make tests` passes.
- [ ] Implement `qed.py` — run `qed verify specs --json` in `<repo>_dev` and parse the payload.
      Test: a captured payload maps each `spec` name to its TOML spec, pairs criteria by index after checking counts and descriptions, reports skipped and failed criteria, and rejects an unknown name or a count mismatch; `make tests` passes.
- [ ] Implement `git.py` — clean tree, status, working-tree and commit diffs, commits, and HEAD.
      Test: a temporary repository reports clean and dirty trees, lists the paths changed in the working tree and in the last commit, and commits a staged path; `make tests` passes.
- [ ] Implement `commit.py` — build the activation message.
      Test: a criterion and an activation report produce the subject and body, with the first sentence normalized to one line and the body preserved; `make tests` passes.
- [ ] Implement `log.py` — append to `harness.log`.
      Test: appending a line creates `harness.log` when absent and adds the line when present; `make tests` passes.
- [ ] Implement `tdd.py` — the outer and inner loops, routing, phase allowlists, preflight, pass limit, and `--model`.
      Test: with fake prompts, qed, git, and container, a pass runs acceptance, commits an activation, routes a missing acceptance test to `atdd-red` and an existing one to the inner cycle, stops on COMPLETE or no open spec, aborts on more than one failing unskipped criterion, enforces each phase allowlist, rejects a target whose `.gitignore` does not ignore `harness.log`, and stops at `--max-passes`; `make tests` passes.
- [ ] Remove `src/tdd.sh` once `tdd.py` replaces it (retain in git history).
- [ ] Remove `schemas/acceptance.schema.json` and `examples/acceptance.json`; `acceptance.json` is no longer task state.

## Later commands

These are out of scope for the `harness tdd` plan. They need their own design; `src/refactor.sh` and `src/acceptance-to-html.sh` are historical references for the retired `acceptance.json` workflow.

- [ ] Implement `scoring.py` — CSV aggregation, score comparison, convergence detection, and loop counter reset.
- [ ] Implement `refactor_loop.py` — outer loop: `qed verify` → `scoring.py`.
- [ ] Implement `acceptance_to_html.py` — render one or more top-level `specs/*.spec.toml` to PicoCSS HTML.
- [ ] Remove `src/refactor.sh` and `src/acceptance-to-html.sh` once their Python commands replace them (retain in git history).
