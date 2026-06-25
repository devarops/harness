"""Write values to golden master received files."""

from pathlib import Path


APPROVAL_DIR = Path("tests/approval")


def printer(value: str, name: str) -> None:
    """Write value to tests/approval/<name>.received.txt."""
    APPROVAL_DIR.mkdir(parents=True, exist_ok=True)
    APPROVAL_DIR.joinpath(f"{name}.received.txt").write_text(value)
