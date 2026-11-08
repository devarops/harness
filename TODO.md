# Backlog

See `PLAN.md` for the agreed design of the `harness tdd` loop.

The scripts in src/ are the behavioral reference for the loop and HTML tasks.

- [ ] Make `make mutants` pass: mutmut 3.8 generates mutants but finds no covering tests under Python 3.15.1; investigate the coverage mapping or pin Python or mutmut.
- [ ] Implement `tdd.py` — the ATDD outer loop, the TDD inner loop, routing, and the pass limit.
- [ ] Implement `prompts.py`, `docker.py`, `qed.py`, `spec.py`, `git.py`, `commit.py`, and `log.py`.
- [ ] Add tests for the loop, routing, and commits.
- [ ] Implement `scoring.py` — CSV aggregation, score comparison, convergence detection, and loop counter reset.
- [ ] Implement `refactor_loop.py` — outer loop: `qed verify` → `scoring.py`.
- [ ] Implement `acceptance_to_html.py` — render `<project>.spec.toml` to PicoCSS HTML.
- [ ] Remove the disposable `src/` bash prototypes once the Python loops replace them (retain in git history).
- [ ] Remove `schemas/acceptance.schema.json` and `examples/acceptance.json`; `acceptance.json` is no longer task state.
