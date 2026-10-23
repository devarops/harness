"""Tests for the harness package metadata."""

import harness
from typer.testing import CliRunner


def test_version():
    assert harness.__version__ == "0.1.0"


def test_version_command():
    from harness.cli import cli

    result = CliRunner().invoke(cli, ["version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "0.1.0"
