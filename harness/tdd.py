"""The harness TDD entry point."""

from pathlib import Path

from harness.spec import is_spec_present

_LOG_NAME = "harness.log"


def tdd() -> None:
    """Run the ATDD/TDD loop against the current repository."""
    root = Path.cwd()
    if not is_spec_present(root):
        _abort("Error: no specs/*.spec.toml found at the repository root.")
    if not _ignores_log(root):
        _abort("Error: .gitignore must ignore harness.log.")


def _abort(message: str) -> None:
    """Print the message and stop the run."""
    print(message)
    raise SystemExit(1)


def _ignores_log(root: Path) -> bool:
    """Return whether the target gitignore names the run log."""
    ignore = root / ".gitignore"
    return ignore.is_file() and _LOG_NAME in ignore.read_text()
