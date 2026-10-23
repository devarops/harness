"""Command-line interface for harness."""

import typer

from harness import __version__

cli = typer.Typer()


@cli.callback()
def main():
    pass


@cli.command()
def version():
    print(__version__)
