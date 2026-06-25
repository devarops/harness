"""Write the current harness version to the approval received file."""

from approval import printer


def version() -> None:
    """Write the current harness version to tests/approval/version.received.txt."""
    from harness import __version__

    printer(__version__, "version")
