"""Approval testing helper for qed-spec harness development."""

import difflib
from pathlib import Path

import pytest

APPROVED_DIR = Path(__file__).parent / "approved"


def _check(name: str) -> None:
    """Compare tests/approval/<name>.received.txt against <name>.approved.txt.

    On first run the .received.txt becomes the .approved.txt automatically.
    When they match the .received.txt is cleaned up.
    When they differ the test fails with a unified diff.
    """
    approved_path = APPROVED_DIR / f"{name}.approved.txt"
    received_path = APPROVED_DIR / f"{name}.received.txt"

    if not approved_path.exists():
        received_path.rename(approved_path)
        return

    if not received_path.exists():
        pytest.fail(
            f"Received file not found: {received_path}\n"
            f"Make sure the test produces {name}.received.txt before "
            f"calling approval."
        )

    expected = approved_path.read_text()
    actual = received_path.read_text()

    if actual == expected:
        received_path.unlink()
        return

    pytest.fail(
        f"Output differs from approved golden master.\n"
        f"  approved: {approved_path}\n"
        f"  received: {received_path}\n"
        f"{_unified_diff(expected, actual)}"
    )


@pytest.fixture
def approval() -> None:
    """Fixture that compares golden master files by name."""
    return _check


def _unified_diff(expected: str, actual: str) -> str:
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
