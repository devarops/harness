"""Run git commands in the target repository."""

import subprocess
from pathlib import Path

_STATUS_COMMAND = ("git", "status", "--porcelain")
_DIFF_COMMAND = ("git", "diff")
_ADD_COMMAND = ("git", "add")
_COMMIT_COMMAND = ("git", "commit", "-m")
_HEAD_COMMAND = ("git", "rev-parse", "--short", "HEAD")
_COMMIT_PATHS_COMMAND = ("git", "show", "--name-only", "--format=", "HEAD")
_RESET_COMMAND = ("git", "reset", "--hard")
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


def diff(root: Path) -> str:
    """Return the working-tree diff.

    Args:
        root: The repository root.

    Returns:
        The text git printed.

    Raises:
        SystemExit: If git cannot print the diff.
    """
    return _run(root, _DIFF_COMMAND)


def add(root: Path, path: str) -> None:
    """Stage one path.

    Args:
        root: The repository root.
        path: The path to stage.

    Raises:
        SystemExit: If git cannot stage the path.
    """
    _run(root, [*_ADD_COMMAND, path])


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


def commit_paths(root: Path) -> list:
    """Return the paths changed by the last commit.

    Args:
        root: The repository root.

    Returns:
        The path of each file the commit touched.

    Raises:
        SystemExit: If git cannot read the commit.
    """
    return _run(root, _COMMIT_PATHS_COMMAND).splitlines()


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


def reset(root: Path, commit: str = "HEAD~1") -> None:
    """Reset the repository to a commit.

    Args:
        root: The repository root.
        commit: The commit to reset to.

    Raises:
        SystemExit: If git cannot reset the repository.
    """
    _run(root, [*_RESET_COMMAND, commit])


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
