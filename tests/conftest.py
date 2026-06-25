"""Approval testing helper for qed-spec harness development."""

from pathlib import Path

import pytest

from approval import _diff_text

APPROVAL_DIR = Path(__file__).parent / "approval"


def _check(name: str) -> None:
    """Compare tests/approval/<name>.received.txt against <name>.approved.txt.

    On first run the .received.txt becomes the .approved.txt automatically.
    When they match the .received.txt is cleaned up.
    When they differ the test fails with a unified diff.
    """
    approved_path = APPROVAL_DIR / f"{name}.approved.txt"
    received_path = APPROVAL_DIR / f"{name}.received.txt"

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
        f"{_diff_text(expected, actual)}"
    )


@pytest.fixture
def approval() -> None:
    """Fixture that compares golden master files by name."""
    return _check

