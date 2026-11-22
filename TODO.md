# Backlog

See `PLAN.md` for the agreed design of the `harness tdd` loop.

The scripts in `src/` are historical references for the retired `acceptance.json` workflow. The qed loop follows the prompts in `~/.config/opencode/commands/` unchanged.

- [*] Implement `cli.py` — expose `--max-passes` and `--model` on `harness tdd`.
      Test: the command help lists both options, and an invocation hands their values to the module; `make tests` passes.
- [ ] Implement `tdd.py` — the outer and inner loops, phase allowlists, preflight, pass limit, and `--model`.
      Test: with fake prompts, qed, git, and container, a pass runs acceptance, commits an activation, runs the acceptance red, gates the inner cycle on a failing make verify and a passing make tests, repeats the refactor prompt while it adds a commit and stops after ten at the pass limit, aborts on more than one failing unskipped criterion or a dirty tree, enforces each phase allowlist, rejects a target whose `.gitignore` does not ignore `harness.log`, writes the counted log lines, and stops at `--max-passes`; `make tests` passes.
- [ ] Remove `src/tdd.sh` once `tdd.py` replaces it (retain in git history).
- [ ] Remove `schemas/acceptance.schema.json` and `examples/acceptance.json`; `acceptance.json` is no longer task state.

## Later commands

These are out of scope for the `harness tdd` plan. They need their own design; `src/refactor.sh` and `src/acceptance-to-html.sh` are historical references for the retired `acceptance.json` workflow.

- [ ] Implement `scoring.py` — CSV aggregation, score comparison, convergence detection, and loop counter reset.
- [ ] Implement `refactor_loop.py` — outer loop: `qed verify` → `scoring.py`.
- [ ] Implement `acceptance_to_html.py` — render one or more top-level `specs/*.spec.toml` to PicoCSS HTML.
- [ ] Remove `src/refactor.sh` and `src/acceptance-to-html.sh` once their Python commands replace them (retain in git history).
