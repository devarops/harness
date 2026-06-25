"""Write the current harness version to the approval received file."""

from pathlib import Path

APPROVED_DIR = Path(__file__).resolve().parent.parent / "tests" / "approved"


def version() -> None:
    """Write the current harness version to tests/approved/version.received.txt."""
    from harness import __version__

    APPROVED_DIR.mkdir(parents=True, exist_ok=True)
    APPROVED_DIR.joinpath("version.received.txt").write_text(__version__)
