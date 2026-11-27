"""The harness TDD entry point."""

import itertools
import sys
import threading
from contextlib import contextmanager
from pathlib import Path

from harness import commit, docker, git, log, prompts, qed, scoring
from harness.spec import import_specs, is_spec_present

_LOG_NAME = "harness.log"
_SPEC_DIR = "specs/"
_PROMPT_DIR = Path.home() / ".config" / "opencode" / "commands"
_CONTAINER_SUFFIX = "_dev"
_FRAMES = "|/-\\"
_FRAME_INTERVAL = 0.2
_SCORE_PROMPT = "afk-score.md"
_MUTANT_PROMPTS = ("afk-mutant-kill.md", "afk-mutant-commit.md")
_BEFORE_COUNTS = "score-before.txt"
_AFTER_COUNTS = "score-after.txt"


def tdd(max_passes: int = 10, model=None) -> None:
    """Run the ATDD/TDD loop against the current repository."""
    root = Path.cwd()
    _preflight(root)
    _startup_gate(root)
    for number in range(1, max_passes + 1):
        complete = _run_pass(root, max_passes, number, model)
        if complete:
            return
    cycle = "cycle" if max_passes == 1 else "cycles"
    _abort(f"≡≡≡ DONE: {max_passes} acceptance {cycle} completed. ≡≡≡")


def _preflight(root: Path) -> None:
    """Refuse a target that cannot run."""
    if not is_spec_present(root):
        _abort("Error: no specs/*.spec.toml found at the repository root.")
    if not _declares_interface(root):
        _abort("Error: AGENTS.md must declare the public interface.")
    if not _ignores_log(root):
        _abort("Error: .gitignore must ignore harness.log.")
    if not _ignores_counts(root):
        _abort("Error: .gitignore must ignore the score count files.")
    if not _has_score_prompt():
        _abort("Error: the score prompt is missing.")
    if not _has_mutation_prompts():
        _abort("Error: a mutation prompt is missing.")
    if not _has_mutants_target(root):
        _abort("Error: the mutants target is missing.")
    if git.changed_paths(root):
        _abort("Error: the working tree is not clean.")


def _startup_gate(root: Path) -> None:
    """Refuse a run whose verification fails before the first pass."""
    if not _verified(_container(root)):
        _abort("Error: make verify fails before the first pass.")


def _run_pass(root: Path, max_passes: int, number: int, model) -> bool:
    """Run acceptance once and refuse a double failure."""
    container = _container(root)
    result = _acceptance(root, max_passes, number, model)
    if result.complete:
        return True
    if _activation(root, container, result.output):
        return False
    _acceptance_red(root, model)
    _inner_loop(root, container, max_passes, number, model)
    return False


def _acceptance(
    root: Path, max_passes: int, number: int, model
) -> prompts.PromptResult:
    """Run the acceptance prompt and return its result."""
    return _run_prompt(
        root,
        f"=== Acceptance cycle {number} of {max_passes} ===",
        "atdd-acceptance.md",
        model,
    )


def _activation(root: Path, container: str, output: str) -> bool:
    """Commit the activation and return whether its criterion passed."""
    report = qed.verify(container, import_specs(root))
    if len(report.failed) > 1:
        _abort("Error: more than one unskipped criterion fails.")
    spec, criterion = _commit_activation(root, output)
    return _criterion_passed(report, spec, criterion)


def _acceptance_red(root: Path, model) -> None:
    """Run the acceptance red and refuse a production commit."""
    head = git.head(root)
    _run_prompt(root, "=== ATDD Red ===", "atdd-red.md", model)
    if _added_production(root, head):
        _abort("Error: the acceptance red committed production.")


def _make(container: str, target: str) -> int:
    """Run a make target in the container and return its exit code."""
    return docker.run(container, ["make", target], docker.WORKDIR).returncode


def _verified(container: str) -> bool:
    """Return whether make verify passes in the container."""
    return _make(container, "verify") == 0


def _tests_pass(container: str) -> bool:
    """Return whether make tests passes in the container."""
    return _make(container, "tests") == 0


def _mutants_pass(container: str) -> bool:
    """Return whether make mutants finds no survivor."""
    return _make(container, "mutants") == 0


def _inner_loop(
    root: Path, container: str, max_passes: int, number: int, model
) -> None:
    """Run inner cycles until the tests and the verification pass."""
    cycle = 0
    while True:
        if _verified(container):
            return
        cycle = _run_until_kept(root, max_passes, number, model, cycle)
        if not _tests_pass(container):
            _abort("Error: make tests fails after the refactor.")


def _run_until_kept(
    root: Path, max_passes: int, number: int, model, cycle: int
) -> int:
    """Run cycles until the gate keeps one and return its number."""
    streak = 0
    while True:
        cycle += 1
        streak = _run_cycle(root, max_passes, number, model, cycle, streak)
        if not streak:
            return cycle


def _run_cycle(
    root: Path, max_passes: int, number: int, model, cycle: int, streak: int
) -> int:
    """Run one inner cycle and return the streak, or zero when it is kept."""
    base = git.head(root)
    _announce(root, f"--- TDD cycle {cycle} (ATDD {number}/{max_passes}) ---")
    _run_prompt(root, "--- TDD Red ---", "afk-red.md", model)
    if _has_production(git.changed_paths(root)):
        _abort("Error: the unit red changed production.")
    head = git.head(root)
    _run_prompt(root, "--- TDD Fail ---", "afk-fail.md", model)
    if _added_production(root, head):
        _abort("Error: the unit fail committed production.")
    _run_prompt(root, "--- TDD Green ---", "afk-green.md", model)
    if _has_test(git.commit_paths(root)):
        _abort("Error: the green phase changed a test.")
    streak = _mutation_gate(root, max_passes, base, streak)
    if streak:
        return streak
    _refactor(root, max_passes, model)
    return 0


def _mutation_gate(root: Path, max_passes: int, base: str, streak: int) -> int:
    """Reset the cycle and return the streak, or zero when it is kept."""
    container = _container(root)
    if _mutants_pass(container):
        return 0
    streak += 1
    _announce(root, f"--- TDD Mutants survived {streak} of {max_passes} ---")
    _reset_cycle(root, base)
    if not _mutants_pass(container):
        _abort("Error: make mutants fails after the reset.")
    return streak


def _reset_cycle(root: Path, base: str) -> None:
    """Return the tree to the cycle base and remove its scraps."""
    git.reset(root, base)
    git.clean(root)


def _refactor(root: Path, max_passes: int, model) -> None:
    """Repeat the refactor while a run adds a commit, up to the limit."""
    head = git.head(root)
    for attempt in range(1, max_passes + 1):
        _run_prompt(
            root,
            f"--- TDD Refactor {attempt} of {max_passes} ---",
            "afk-refactor.md",
            model,
        )
        if git.changed_paths(root):
            _abort("Error: a prompt left the working tree dirty.")
        moved = git.head(root)
        if moved == head:
            return
        files = git.commit_paths(root)
        if _has_fixture(files):
            _abort("Error: the refactor committed a fixture.")
        before_median, after_median = _score_attempt(root, head, moved, files, model)
        if _is_worse(before_median, after_median):
            _undo_refactor(root)
            return
        if _is_equal(before_median, after_median):
            return
        if _is_unmeasured(before_median, after_median):
            return
        head = moved


def _is_worse(before, after) -> bool:
    """Return whether the after median is higher than the before median."""
    if before is None or after is None:
        return False
    return after > before


def _is_equal(before, after) -> bool:
    """Return whether both medians exist and match."""
    if before is None or after is None:
        return False
    return after == before


def _is_unmeasured(before, after) -> bool:
    """Return whether either median is missing."""
    return before is None or after is None


def _score_attempt(root: Path, before: str, after: str, files: list, model) -> tuple:
    """Score the touched files at the pre-refactor and new commits."""
    prompt = _PROMPT_DIR / _SCORE_PROMPT
    before_counts = root / _BEFORE_COUNTS
    after_counts = root / _AFTER_COUNTS
    before_counts.unlink(missing_ok=True)
    after_counts.unlink(missing_ok=True)
    before_median = scoring.score(before, files, before_counts, prompt, model)
    after_median = scoring.score(after, files, after_counts, prompt, model)
    _record_median(root, "before", before_median)
    _record_median(root, "after", after_median)
    return before_median, after_median


def _undo_refactor(root: Path) -> None:
    """Reset the refactor commit and refuse a dirty tree."""
    git.reset(root)
    if git.changed_paths(root):
        _abort("Error: the reset left the working tree dirty.")


def _record_median(root: Path, side: str, median) -> None:
    """Write the median of one side to the log unless it is missing."""
    if median is not None:
        _announce(root, f"--- TDD Median weakness count {side} {median:g} ---")


def _commit_activation(root: Path, report: str) -> tuple:
    """Commit the activation acceptance left behind."""
    changed = git.changed_paths(root)
    if len(changed) != 1 or not changed[0].startswith(_SPEC_DIR):
        _abort("Error: acceptance must change exactly one spec.")
    diff_text = git.diff(root)
    removed = [
        line
        for line in diff_text.splitlines()
        if line.startswith("-") and not line.startswith("---")
    ]
    if not _is_skip_removal(removed):
        _abort("Error: acceptance must remove exactly one skip line.")
    spec = next(
        item for item in import_specs(root) if item.path == root / changed[0]
    )
    criterion = _skip_owner(spec, diff_text, removed[0])
    git.add(root, changed[0])
    git.commit(root, commit.activation_message(criterion, report))
    return spec, criterion


def _criterion_passed(report, spec, criterion) -> bool:
    """Return whether the report passed the criterion."""
    return report.results[spec.name][spec.criteria.index(criterion)] == "passed"


def _skip_owner(spec, diff_text: str, removed: str):
    """Return the criterion whose description precedes the removed skip."""
    lines = diff_text.splitlines()
    for line in reversed(lines[: lines.index(removed)]):
        text = line[1:].strip()
        if text.startswith("description ="):
            description = text.split("=", 1)[1].strip().strip('"')
            return next(
                item for item in spec.criteria if item.description == description
            )
    return next(item for item in spec.criteria if item.skip is None)


def _is_skip_removal(removed: list) -> bool:
    """Return whether the diff removed exactly one skip line."""
    if len(removed) != 1:
        return False
    return removed[0].lstrip("-").strip().startswith("skip")


def _is_test(path: str) -> bool:
    """Return whether the path is a test."""
    return path.startswith("tests/") or path.startswith("spec/")


def _has_test(paths: list) -> bool:
    """Return whether any path is a test."""
    return any(_is_test(path) for path in paths)


def _has_fixture(paths: list) -> bool:
    """Return whether any path is a fixture."""
    return any(path.startswith("tests/data/") for path in paths)


def _added_production(root: Path, head: str) -> bool:
    """Return whether the prompt added a commit of production."""
    return git.head(root) != head and _has_production(git.commit_paths(root))


def _has_production(paths: list) -> bool:
    """Return whether any path is not a test."""
    return any(not _is_test(path) for path in paths)


def _announce(root: Path, line: str) -> None:
    """Write the line to the log and print it."""
    log.append(root, line)
    print(line, flush=True)


@contextmanager
def _waiting():
    """Cycle frames on the terminal while the caller waits."""
    if not sys.stdout.isatty():
        yield
        return
    stop = threading.Event()

    def spin():
        for frame in itertools.cycle(_FRAMES[1:]):
            if stop.wait(_FRAME_INTERVAL):
                return
            print(f"\r{frame}", end="", flush=True)

    print(f"\r{_FRAMES[0]}", end="", flush=True)
    thread = threading.Thread(target=spin, daemon=True)
    thread.start()
    try:
        yield
    finally:
        stop.set()
        thread.join()
        print("\r \r", end="", flush=True)


def _run_prompt(root: Path, header: str, name: str, model) -> prompts.PromptResult:
    """Write the prompt's header, run it, and write its output."""
    _announce(root, header)
    with _waiting():
        result = prompts.run_prompt(_PROMPT_DIR / name, model)
    log.append(root, result.output)
    if result.failure:
        _abort(f"Error: {result.failure}")
    return result


def _abort(message: str) -> None:
    """Print the message and stop the run."""
    print(message)
    raise SystemExit(1)


def _declares_interface(root: Path) -> bool:
    """Return whether the target names its public interface."""
    agents = root / "AGENTS.md"
    return agents.is_file() and "public interface" in agents.read_text().lower()


def _ignores_log(root: Path) -> bool:
    """Return whether the target gitignore names the run log."""
    return _LOG_NAME in _gitignore(root)


def _ignores_counts(root: Path) -> bool:
    """Return whether the target gitignore names both count files."""
    text = _gitignore(root)
    return _BEFORE_COUNTS in text and _AFTER_COUNTS in text


def _has_score_prompt() -> bool:
    """Return whether the score prompt exists."""
    return _prompt_exists(_SCORE_PROMPT)


def _has_mutation_prompts() -> bool:
    """Return whether both mutation prompts exist."""
    return all(_prompt_exists(name) for name in _MUTANT_PROMPTS)


def _prompt_exists(name: str) -> bool:
    """Return whether the named prompt exists."""
    return (_PROMPT_DIR / name).is_file()


def _has_mutants_target(root: Path) -> bool:
    """Return whether make can dry-run the mutants target."""
    container = _container(root)
    command = ["make", "-n", "mutants"]
    return docker.run(container, command, docker.WORKDIR).returncode == 0


def _container(root: Path) -> str:
    """Return the target's development container name."""
    return f"{root.name}{_CONTAINER_SUFFIX}"


def _gitignore(root: Path) -> str:
    """Return the target gitignore text, or an empty string without one."""
    ignore = root / ".gitignore"
    return ignore.read_text() if ignore.is_file() else ""
