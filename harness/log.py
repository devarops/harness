"""Append to the run log."""

from pathlib import Path

_LOG_NAME = "harness.log"


def append(root: Path, line: str) -> None:
    """Append a line to the run log.

    Args:
        root: The repository root.
        line: The line to append.
    """
    with (root / _LOG_NAME).open("a") as log:
        log.write(f"{line}\n")
