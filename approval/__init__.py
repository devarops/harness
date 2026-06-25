"""Write values to golden master received files."""

import difflib
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
    """Promote tests/approval/<name>.received.txt to <name>.approved.txt."""
    _received_path(name).rename(_approved_path(name))


def review(name: str) -> str:
    """Return a unified diff between the approved and received files."""
    approved_lines = _approved_path(name).read_text().splitlines(keepends=True)
    received_lines = _received_path(name).read_text().splitlines(keepends=True)
    diff = difflib.unified_diff(
        approved_lines,
        received_lines,
        fromfile="approved",
        tofile="received",
    )
    return "".join(diff)
