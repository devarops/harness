# Backlog

See `PLAN.md` for the agreed design of the `harness tdd` loop.

The scripts in `src/` are historical references for the retired `acceptance.json` workflow. The qed loop follows the prompts in `~/.config/opencode/commands/` unchanged.

- [x] Run `atdd-acceptance` only when `make verify` passes.
      Test: with fake prompts and a container whose `make verify` fails and then passes, `harness tdd` runs `afk-red`, `afk-fail`, `afk-green`, and `afk-refactor` before `atdd-acceptance`, and acceptance runs only after the passing verification; `make tests` passes.

- [ ] Repeat the inner cycle until `make verify` passes.
      Test: after an activation whose acceptance test fails, with a container whose `make verify` fails twice and then passes, `harness tdd` runs `afk-red` again after each refactor and runs `atdd-acceptance` again only after the passing verification; `make tests` passes.

## Later commands

These are out of scope for the `harness tdd` plan. They need their own design; `src/refactor.sh` and `src/acceptance-to-html.sh` are historical references for the retired `acceptance.json` workflow.

- [ ] Implement `scoring.py` — CSV aggregation, score comparison, convergence detection, and loop counter reset.
- [ ] Implement `refactor_loop.py` — outer loop: `qed verify` → `scoring.py`.
- [ ] Implement `acceptance_to_html.py` — render one or more top-level `specs/*.spec.toml` to PicoCSS HTML.
- [ ] Remove `src/refactor.sh` and `src/acceptance-to-html.sh` once their Python commands replace them (retain in git history).
