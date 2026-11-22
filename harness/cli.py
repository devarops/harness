"""Command-line interface for harness."""

from typing import Annotated, Optional

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
def tdd(
    max_passes: Annotated[int, typer.Option()] = 10,
    model: Annotated[Optional[str], typer.Option()] = None,
) -> None:
    """Develop the repository's acceptance spec through ATDD/TDD cycles."""
    tdd_module.tdd(max_passes, model)
