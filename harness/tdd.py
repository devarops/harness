"""The harness TDD entry point."""

from pathlib import Path

from harness import commit, git, prompts, qed
from harness.spec import import_specs, is_spec_present

_LOG_NAME = "harness.log"
_SPEC_DIR = "specs/"
_PROMPT_DIR = Path.home() / ".config" / "opencode" / "commands"
_CONTAINER_SUFFIX = "_dev"


def tdd(max_passes: int = 10, model=None) -> None:
    """Run the ATDD/TDD loop against the current repository."""
    root = Path.cwd()
    _preflight(root)
    _run_pass(root)


def _preflight(root: Path) -> None:
    """Refuse a target that cannot run."""
    if not is_spec_present(root):
        _abort("Error: no specs/*.spec.toml found at the repository root.")
    if not _ignores_log(root):
        _abort("Error: .gitignore must ignore harness.log.")
    if git.changed_paths(root):
        _abort("Error: the working tree is not clean.")


def _run_pass(root: Path) -> None:
    """Run acceptance once and refuse a double failure."""
    container = f"{root.name}{_CONTAINER_SUFFIX}"
    result = prompts.run_prompt(_PROMPT_DIR / "atdd-acceptance.md")
    if result.complete:
        return
    report = qed.verify(container, root, import_specs(root))
    if len(report.failed) > 1:
        _abort("Error: more than one unskipped criterion fails.")
    _commit_activation(root, result.output)


def _commit_activation(root: Path, report: str) -> None:
    """Commit the activation acceptance left behind."""
    changed = git.changed_paths(root)
    if len(changed) != 1 or not changed[0].startswith(_SPEC_DIR):
        _abort("Error: acceptance must change exactly one spec.")
    removed = [
        line
        for line in git.diff(root).splitlines()
        if line.startswith("-") and not line.startswith("---")
    ]
    if not _is_skip_removal(removed):
        _abort("Error: acceptance must remove exactly one skip line.")
    spec = next(
        item for item in import_specs(root) if item.path == root / changed[0]
    )
    criterion = next(item for item in spec.criteria if item.skip is None)
    git.add(root, changed[0])
    git.commit(root, commit.activation_message(criterion, report))


def _is_skip_removal(removed: list) -> bool:
    """Return whether the diff removed exactly one skip line."""
    if len(removed) != 1:
        return False
    return removed[0].lstrip("-").strip().startswith("skip")


def _abort(message: str) -> None:
    """Print the message and stop the run."""
    print(message)
    raise SystemExit(1)


def _ignores_log(root: Path) -> bool:
    """Return whether the target gitignore names the run log."""
    ignore = root / ".gitignore"
    return ignore.is_file() and _LOG_NAME in ignore.read_text()
