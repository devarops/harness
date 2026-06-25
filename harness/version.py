"""Write the current harness version to the approval received file."""

from pathlib import Path

APPROVAL_DIR = Path(__file__).resolve().parent.parent / "tests" / "approval"


def version() -> None:
    """Write the current harness version to tests/approval/version.received.txt."""
    from harness import __version__

    APPROVAL_DIR.mkdir(parents=True, exist_ok=True)
    APPROVAL_DIR.joinpath("version.received.txt").write_text(__version__)
