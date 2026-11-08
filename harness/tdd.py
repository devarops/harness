"""The harness TDD entry point."""

from pathlib import Path

from harness.spec import is_spec_present


def tdd() -> None:
    """Run the ATDD/TDD loop against the current repository."""
    if not is_spec_present(Path.cwd()):
        print("Error: no specs/*.spec.toml found at the repository root.")
        raise SystemExit(1)
