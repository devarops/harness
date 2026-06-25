# Gold

- `approve(name)` — mv `<name>.received.txt` → `<name>.approved.txt`

# Backlog

## Design decisions (interview log)

### Scope
- Replace all three `src/*.sh` scripts with qed specs + Python module.
- `specs/tdd.spec.toml` — TDD scaffold criteria (reusable across projects).
- `specs/refactor.spec.toml` — Refactoring/daemon criteria.
- Consuming projects provide `<project>.spec.toml` at their repo root (acceptance criteria as qed spec).
- `harness/` Python package — Typer CLI, module structure.

### Execution mode
- **qed verify mode** — no worker, no built-in retry.
- **Outer deterministic loop** in Python (`harness tdd`, `harness refactor`).
- `command` criterion unexpected exit → loop aborts. `agent` criterion failure does not abort (informative).

### TDD conveyor-belt model
- Each cycle: `merge_specs.py` prepends the first unfulfilled criterion from `<project>.spec.toml` onto `tdd.spec.toml`.
- `qed verify --json` runs all criteria.
- If acceptance criterion (position 1, `agent`) passes → advance to next criterion.
- If it fails → leave on top, retry next cycle.
- If any `command` criterion fails → abort loop.

### TDD criteria chain
```
1.  [acceptance criterion from <project>.spec.toml]  agent
2.  red                                               agent
3.  tests_fail                                        command  `! make tests`
4.  green                                             agent
5.  tests_pass                                        command  `make tests`
6.  refactor                                          agent
7.  tests_pass2                                       command  `make tests`
8.  mutants                                           command  `make mutants`
9.  approve                                           human    interactive sign-off
```

### Refactoring criteria chain
```
1.  refactor        agent
2.  tests_pass      command  `make tests`
3.  acceptance      agent
4.  mutants         command  `make mutants`
5a. score_model_1   agent    (appends to score_detail.csv)
5b. score_valid_1   command  frictionless validate
6a. score_model_2   agent
6b. score_valid_2   command  frictionless validate
7a. score_model_3   agent
7b. score_valid_3   command  frictionless validate
```

- Scoring is pulled out of qed: outer loop calls `scoring.py` after `qed verify` to aggregate CSV, check trend, detect convergence, and reset counter if score improved.

### Repository structure
```
harness/
├── pyproject.toml            # flit build, Typer CLI
├── Makefile                  # standard targets (init, tests, check, format, mutants, coverage, linter, clean)
├── Dockerfile                # Python base + dependencies
├── docker-compose.yml
├── specs/
│   ├── tdd.spec.toml         # TDD scaffold criteria
│   └── refactor.spec.toml    # Refactoring criteria
├── approval/                 # Approval testing helper package
│   ├── __init__.py           # printer, approve, reject, review
│   └── __main__.py           # python -m approval approve <name>
├── harness/                  # Python package (Typer CLI)
│   ├── __init__.py
│   ├── __main__.py           # python -m harness
│   ├── cli.py                # harness tdd, refactor, acceptance-to-html
│   ├── tdd_loop.py           # Conveyor-belt outer loop
│   ├── refactor_loop.py      # Refactoring daemon outer loop
│   ├── scoring.py            # Score aggregation, trend, convergence
│   ├── merge_specs.py        # Merge tdd.spec.toml + project spec
│   └── acceptance_to_html.py # Render spec → HTML
├── schemas/                  # score_detail.yaml, score_aggregate.yaml
├── tests/
│   ├── approval/             # Golden master files (.approved.txt, .received.txt)
│   ├── conftest.py           # approval() fixture
│   ├── test_*.py             # Tests for the harness
├── examples/
│   └── acceptance.json       # kept as reference (deprecated format)
├── .github/workflows/        # CI
└── *.md
```

### Approval testing module

- `approval/` Python package at project root (sibling to `harness/`).
- `pyproject.toml` changed from `module = "harness"` to `modules = ["harness", "approval"]`.
- Golden master files live in `tests/approval/` directory (renamed from `tests/approved/`).
- Directory path hard-coded, relative to project root.
- Four functions in `approval/__init__.py`:
  - `printer(value, name)` — writes value to `tests/approval/<name>.received.txt`
  - `approve(name)` — mv `<name>.received.txt` → `<name>.approved.txt`
  - `reject(name)` — rm `<name>.received.txt`
  - `review(name)` — shows unified diff between approved and received
- CLI entry point via `approval/__main__.py` (`python -m approval approve <name>`).
- Make targets: `make approve NAME=x`, `make reject NAME=x`, `make review NAME=x`.
- `approval()` fixture stays in `tests/conftest.py` (pytest-specific, not part of the module).
  - Auto-promotes received → approved on first run (no golden master yet).
  - Delegates diff comparison to its own logic (not importing from approval/ module).
- `harness/version.py` uses `approval.printer()` instead of direct file writes.

### Language / tools
- **Python 3.11+** (Docker image base).
- **flit** for build/packaging (`pyproject.toml`).
- **Typer** for CLI.
- **qed** for spec-driven verification (external binary).
- **Docker** for isolated execution (consuming project tests run in container).
- **frictionless** for CSV schema validation.

---

# Implementation steps

1.  Scaffold Python package: `pyproject.toml`, `Makefile`, `Dockerfile`, `docker-compose.yml`, `.github/workflows`, `harness/__init__.py`, `harness/__main__.py`.
1.  Create `approval/` package with `printer`, `approve`, `reject`, `review` and `__main__.py` CLI.
1.  Rename `tests/approved/` to `tests/approval/` and update `conftest.py` + `harness/version.py`.
1.  Add Make targets: `make approve`, `make reject`, `make review`.
2.  Implement `merge_specs.py` — reads `specs/tdd.spec.toml` and `<project>.spec.toml`, prepends first unfulfilled criterion into combined spec.
3.  Implement `tdd_loop.py` — outer loop: merge → `qed verify --json` → parse JSON → advance conveyor belt or abort.
4.  Implement `refactor_loop.py` — outer loop: `qed verify refactor.spec.toml` → `scoring.py`.
5.  Implement `scoring.py` — CSV aggregation, score comparison, convergence detection, loop counter reset.
6.  Implement `acceptance_to_html.py` — render `<project>.spec.toml` to PicoCSS HTML.
7.  Implement `cli.py` — Typer commands wiring the above.
8.  Write specs: `specs/tdd.spec.toml`, `specs/refactor.spec.toml` with all criteria chains.
9.  Adapt `acceptance-to-html.sh` to read qed TOML spec format instead of `acceptance.json`.
10. Write tests for the harness itself (`tests/`).
11. Remove old `src/` bash scripts (retain in git history).
