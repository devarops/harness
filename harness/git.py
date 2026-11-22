"""Run git commands in the target repository."""

import subprocess
from pathlib import Path

_STATUS_COMMAND = ("git", "status", "--porcelain")
_COMMIT_COMMAND = ("git", "commit", "-m")
_HEAD_COMMAND = ("git", "rev-parse", "--short", "HEAD")
_FAILURE_EXIT_CODE = 1
_STATUS_PREFIX_LENGTH = 3


def status(root: Path) -> list:
    """Return the paths changed in the working tree.

    Args:
        root: The repository root.

    Returns:
        The status lines git printed.

    Raises:
        SystemExit: If git cannot report the status.
    """
    return _run(root, _STATUS_COMMAND).splitlines()


def commit(root: Path, message: str) -> None:
    """Record the staged changes.

    Args:
        root: The repository root.
        message: The commit message.

    Raises:
        SystemExit: If git cannot make the commit.
    """
    _run(root, [*_COMMIT_COMMAND, message])


def changed_paths(root: Path) -> list:
    """Return the paths changed in the working tree.

    Args:
        root: The repository root.

    Returns:
        The path of each status entry, without its status code.

    Raises:
        SystemExit: If git cannot report the status.
    """
    return [entry[_STATUS_PREFIX_LENGTH:] for entry in status(root)]


def head(root: Path) -> str:
    """Return the short commit hash at HEAD.

    Args:
        root: The repository root.

    Returns:
        The short hash git printed.

    Raises:
        SystemExit: If git cannot resolve HEAD.
    """
    return _run(root, _HEAD_COMMAND).strip()


def _run(root: Path, command: list) -> str:
    """Return the output of a git command.

    Args:
        root: The repository root.
        command: The command and its arguments.

    Returns:
        The text git printed.

    Raises:
        SystemExit: If git cannot run the command.
    """
    completed = subprocess.run(command, cwd=root, capture_output=True, text=True)
    if completed.returncode != 0:
        raise SystemExit(_FAILURE_EXIT_CODE)
    return completed.stdout
