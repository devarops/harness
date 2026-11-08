"""Command-line interface for harness."""

import typer

from harness import __version__
from harness import tdd as tdd_module

cli = typer.Typer()


@cli.callback()
def main():
    pass


@cli.command()
def version():
    print(__version__)


@cli.command()
def tdd() -> None:
    """Develop the repository's acceptance spec through ATDD/TDD cycles."""
    tdd_module.tdd()
