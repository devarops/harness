"""Write values to golden master received files."""

from pathlib import Path


APPROVAL_DIR = Path("tests/approval")


def _received_path(name: str) -> Path:
    """Return the path to the received file for the given name."""
    return APPROVAL_DIR.joinpath(f"{name}.received.txt")


def printer(value: str, name: str) -> None:
    """Write value to tests/approval/<name>.received.txt."""
    APPROVAL_DIR.mkdir(parents=True, exist_ok=True)
    _received_path(name).write_text(value)


def reject(name: str) -> None:
    """Remove tests/approval/<name>.received.txt."""
    _received_path(name).unlink(missing_ok=True)
