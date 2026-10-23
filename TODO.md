# Backlog

The scripts in src/ are the behavioral reference for the loop and HTML tasks.

- [ ] Make `make mutants` pass: mutmut 3.8 generates mutants but finds no covering tests under Python 3.15.1; investigate the coverage mapping or pin Python or mutmut.
- [ ] Implement `tdd.py` — outer loop: `qed verify --json` → parse JSON → advance or abort.
- [ ] Implement `scoring.py` — CSV aggregation, score comparison, convergence detection, and loop counter reset.
- [ ] Implement `refactor_loop.py` — outer loop: `qed verify` → `scoring.py`.
- [ ] Implement `acceptance_to_html.py` — render `<project>.spec.toml` to PicoCSS HTML.
- [ ] Remove the disposable `src/` bash prototypes once the Python loops replace them (retain in git history).
