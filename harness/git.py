"""Run git commands in the target repository."""

import subprocess
from pathlib import Path

_STATUS_COMMAND = ("git", "status", "--porcelain")
_COMMIT_COMMAND = ("git", "commit", "-m")
_FAILURE_EXIT_CODE = 1


def status(root: Path) -> list:
    """Return the paths changed in the working tree.

    Args:
        root: The repository root.

    Returns:
        The status lines git printed.

    Raises:
        SystemExit: If git cannot report the status.
    """
    completed = subprocess.run(
        _STATUS_COMMAND, cwd=root, capture_output=True, text=True
    )
    if completed.returncode != 0:
        raise SystemExit(_FAILURE_EXIT_CODE)
    return completed.stdout.splitlines()


def commit(root: Path, message: str) -> None:
    """Record the staged changes.

    Args:
        root: The repository root.
        message: The commit message.

    Raises:
        SystemExit: If git cannot make the commit.
    """
    completed = subprocess.run(
        [*_COMMIT_COMMAND, message], cwd=root, capture_output=True, text=True
    )
    if completed.returncode != 0:
        raise SystemExit(_FAILURE_EXIT_CODE)
