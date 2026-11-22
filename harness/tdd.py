"""The harness TDD entry point."""

from pathlib import Path

from harness import git, prompts, qed
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
    _check_activation(root)


def _check_activation(root: Path) -> None:
    """Refuse an edit that is not one removed line in one spec."""
    changed = git.changed_paths(root)
    if len(changed) != 1 or not changed[0].startswith(_SPEC_DIR):
        _abort("Error: acceptance must change exactly one spec.")
    removed = [
        line
        for line in git.diff(root).splitlines()
        if line.startswith("-") and not line.startswith("---")
    ]
    if len(removed) != 1:
        _abort("Error: acceptance must remove exactly one line.")


def _abort(message: str) -> None:
    """Print the message and stop the run."""
    print(message)
    raise SystemExit(1)


def _ignores_log(root: Path) -> bool:
    """Return whether the target gitignore names the run log."""
    ignore = root / ".gitignore"
    return ignore.is_file() and _LOG_NAME in ignore.read_text()
