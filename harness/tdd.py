"""The harness TDD entry point."""

from pathlib import Path


def do_nothing():
    """Placeholder entry point for the first test of this module."""


def tdd() -> None:
    """Run the ATDD/TDD loop against the current repository."""
    if not list(Path("specs").glob("*.spec.toml")):
        print("Error: no specs/*.spec.toml found at the repository root.")
        raise SystemExit(1)
