"""Write the current harness version to the approval received file."""

from approval import printer


def version() -> str:
    """Return the current harness version and write it to tests/approval/version.received.txt."""
    from harness import __version__
    printer(__version__, "version")
    return __version__
