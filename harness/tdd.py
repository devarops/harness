"""The harness TDD entry point."""

from pathlib import Path

from harness import commit, docker, git, prompts, qed
from harness.spec import import_specs, is_spec_present

_LOG_NAME = "harness.log"
_SPEC_DIR = "specs/"
_PROMPT_DIR = Path.home() / ".config" / "opencode" / "commands"
_CONTAINER_SUFFIX = "_dev"


def tdd(max_passes: int = 10, model=None) -> None:
    """Run the ATDD/TDD loop against the current repository."""
    root = Path.cwd()
    _preflight(root)
    for _ in range(max_passes):
        complete = _run_pass(root, max_passes)
        if complete:
            return
    _abort("Error: the pass limit was reached.")


def _preflight(root: Path) -> None:
    """Refuse a target that cannot run."""
    if not is_spec_present(root):
        _abort("Error: no specs/*.spec.toml found at the repository root.")
    if not _ignores_log(root):
        _abort("Error: .gitignore must ignore harness.log.")
    if git.changed_paths(root):
        _abort("Error: the working tree is not clean.")


def _run_pass(root: Path, max_passes: int) -> None:
    """Run acceptance once and refuse a double failure."""
    container = f"{root.name}{_CONTAINER_SUFFIX}"
    result = prompts.run_prompt(_PROMPT_DIR / "atdd-acceptance.md")
    if result.complete:
        return True
    report = qed.verify(container, root, import_specs(root))
    if len(report.failed) > 1:
        _abort("Error: more than one unskipped criterion fails.")
    _commit_activation(root, result.output)
    prompts.run_prompt(_PROMPT_DIR / "atdd-red.md")
    _gate(root, container, max_passes)
    return False


def _gate(root: Path, container: str, max_passes: int) -> None:
    """End the pass or open the unit cycle."""
    if docker.run(container, ["make", "tests"], root).returncode != 0:
        _abort("Error: make tests fails after the acceptance red.")
    if docker.run(container, ["make", "verify"], root).returncode == 0:
        return
    _run_cycle(root, max_passes)


def _run_cycle(root: Path, max_passes: int) -> None:
    """Run one inner cycle."""
    prompts.run_prompt(_PROMPT_DIR / "afk-red.md")
    prompts.run_prompt(_PROMPT_DIR / "afk-fail.md")
    prompts.run_prompt(_PROMPT_DIR / "afk-green.md")
    if any(_is_test(item) for item in git.commit_paths(root)):
        _abort("Error: the green phase changed a test.")
    _refactor(root, max_passes)


def _refactor(root: Path, max_passes: int) -> None:
    """Repeat the refactor while a run adds a commit, up to the limit."""
    head = git.head(root)
    for _ in range(max_passes):
        prompts.run_prompt(_PROMPT_DIR / "afk-refactor.md")
        if git.changed_paths(root):
            _abort("Error: a prompt left the working tree dirty.")
        moved = git.head(root)
        if moved == head:
            return
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


def _abort(message: str) -> None:
    """Print the message and stop the run."""
    print(message)
    raise SystemExit(1)


def _ignores_log(root: Path) -> bool:
    """Return whether the target gitignore names the run log."""
    ignore = root / ".gitignore"
    return ignore.is_file() and _LOG_NAME in ignore.read_text()
