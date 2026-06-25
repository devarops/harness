"""Write values to golden master received files."""

import difflib
import shutil
from pathlib import Path


APPROVAL_DIR = Path("tests/approval")


def _received_path(name: str) -> Path:
    """Return the path to the received file for the given name."""
    return APPROVAL_DIR.joinpath(f"{name}.received.txt")


def _approved_path(name: str) -> Path:
    """Return the path to the approved file for the given name."""
    return APPROVAL_DIR.joinpath(f"{name}.approved.txt")


def printer(value: str, name: str) -> None:
    """Write value to tests/approval/<name>.received.txt."""
    APPROVAL_DIR.mkdir(parents=True, exist_ok=True)
    _received_path(name).write_text(value)


def reject(name: str) -> None:
    """Remove tests/approval/<name>.received.txt."""
    _received_path(name).unlink(missing_ok=True)


def approve(name: str) -> None:
    """Copy tests/approval/<name>.received.txt to <name>.approved.txt.

    The received file is preserved so subsequent review() calls
    can compare both files.
    """
    shutil.copy2(_received_path(name), _approved_path(name))


def _diff_text(expected: str, actual: str) -> str:
    """Generate a unified diff string between expected and actual."""
    exp_lines = expected.splitlines(keepends=True)
    act_lines = actual.splitlines(keepends=True)
    diff_lines = list(
        difflib.unified_diff(
            exp_lines,
            act_lines,
            fromfile="approved",
            tofile="received",
        )
    )
    return "".join(diff_lines)


def review(name: str) -> str:
    """Return a unified diff between the approved and received files."""
    return _diff_text(
        _approved_path(name).read_text(),
        _received_path(name).read_text(),
    )
