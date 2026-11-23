"""The harness TDD entry point."""

from pathlib import Path

from harness import commit, docker, git, log, prompts, qed
from harness.spec import import_specs, is_spec_present

_LOG_NAME = "harness.log"
_SPEC_DIR = "specs/"
_PROMPT_DIR = Path.home() / ".config" / "opencode" / "commands"
_CONTAINER_SUFFIX = "_dev"


def tdd(max_passes: int = 10, model=None) -> None:
    """Run the ATDD/TDD loop against the current repository."""
    root = Path.cwd()
    _preflight(root)
    for number in range(1, max_passes + 1):
        complete = _run_pass(root, max_passes, number, model)
        if complete:
            return
    _abort("Error: the pass limit was reached.")


def _preflight(root: Path) -> None:
    """Refuse a target that cannot run."""
    if not is_spec_present(root):
        _abort("Error: no specs/*.spec.toml found at the repository root.")
    if not _declares_interface(root):
        _abort("Error: AGENTS.md must declare the public interface.")
    if not _ignores_log(root):
        _abort("Error: .gitignore must ignore harness.log.")
    if git.changed_paths(root):
        _abort("Error: the working tree is not clean.")


def _run_pass(root: Path, max_passes: int, number: int, model) -> bool:
    """Run acceptance once and refuse a double failure."""
    container = f"{root.name}{_CONTAINER_SUFFIX}"
    if _make(container, "verify") != 0:
        _run_cycle(root, max_passes, number, model)
    result = _run_prompt(
        root,
        f"=== Acceptance cycle {number} of {max_passes} ===",
        "atdd-acceptance.md",
        model,
    )
    if result.complete:
        return True
    report = qed.verify(container, import_specs(root))
    if len(report.failed) > 1:
        _abort("Error: more than one unskipped criterion fails.")
    _commit_activation(root, result.output)
    head = git.head(root)
    _run_prompt(root, "=== ATDD Red ===", "atdd-red.md", model)
    if _added_production(root, head):
        _abort("Error: the acceptance red committed production.")
    _gate(root, container, max_passes, number, model)
    return False


def _gate(root: Path, container: str, max_passes: int, number: int, model) -> None:
    """End the pass or open the unit cycle."""
    if _make(container, "tests") != 0:
        _abort("Error: make tests fails after the acceptance red.")
    if _make(container, "verify") == 0:
        return
    _run_cycle(root, max_passes, number, model)


def _make(container: str, target: str) -> int:
    """Run a make target in the container and return its exit code."""
    return docker.run(container, ["make", target], docker.WORKDIR).returncode


def _run_cycle(root: Path, max_passes: int, number: int, model) -> None:
    """Run one inner cycle."""
    log.append(root, f"--- TDD cycle 1 (ATDD {number}/{max_passes}) ---")
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
    _refactor(root, max_passes, model)


def _refactor(root: Path, max_passes: int, model) -> None:
    """Repeat the refactor while a run adds a commit, up to the limit."""
    head = git.head(root)
    for attempt in range(1, max_passes + 1):
        _run_prompt(
            root,
            f"--- Refactor {attempt} of {max_passes} ---",
            "afk-refactor.md",
            model,
        )
        if git.changed_paths(root):
            _abort("Error: a prompt left the working tree dirty.")
        moved = git.head(root)
        if moved == head:
            return
        if _has_fixture(git.commit_paths(root)):
            _abort("Error: the refactor committed a fixture.")
        head = moved


def _commit_activation(root: Path, report: str) -> None:
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


def _run_prompt(root: Path, header: str, name: str, model):
    """Write the prompt's header, run it, and write its output."""
    log.append(root, header)
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
    ignore = root / ".gitignore"
    return ignore.is_file() and _LOG_NAME in ignore.read_text()
