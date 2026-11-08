# Backlog

See `PLAN.md` for the agreed design of the `harness tdd` loop.

The scripts in src/ are the behavioral reference for the loop and HTML tasks.

- [ ] Implement `tdd.py` — the ATDD outer loop, the TDD inner loop, routing, and the pass limit.
- [ ] Implement `prompts.py`, `docker.py`, `qed.py`, `git.py`, `commit.py`, and `log.py`.
- [*] Finish `spec.py` discovery — return every top-level `specs/*.spec.toml` with its name and reject duplicate names.
      Test: every top-level spec returns its path and name, duplicate names abort, and `make tests` passes.
- [ ] Parse the criteria of each spec in `spec.py` — description, skip, and verify command.
      Test: every criterion returns its description, its skip reason when present, and its verify command, and `make tests` passes.
- [ ] Map qed's spec names to their TOML files in `spec.py`.
      Test: every name in a qed payload resolves to its spec file, an unknown name aborts, and `make tests` passes.
- [ ] Enforce the open-spec invariant in `tdd.py` — zero open specs end the run, one is active, and several abort.
- [ ] Update the prompts to accept several specs and work on the open one; the dotfiles copy of `atdd-acceptance` still rejects them.
- [ ] Add tests for the loop, routing, commits, and the open-spec invariant.
- [ ] Implement `scoring.py` — CSV aggregation, score comparison, convergence detection, and loop counter reset.
- [ ] Implement `refactor_loop.py` — outer loop: `qed verify` → `scoring.py`.
- [ ] Implement `acceptance_to_html.py` — render `<project>.spec.toml` to PicoCSS HTML.
- [ ] Remove the disposable `src/` bash prototypes once the Python loops replace them (retain in git history).
- [ ] Remove `schemas/acceptance.schema.json` and `examples/acceptance.json`; `acceptance.json` is no longer task state.
