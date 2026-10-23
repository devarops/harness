"""Acceptance tests for the harness CLI."""

import subprocess

from typer.testing import CliRunner


def test_version_command():
    from harness.cli import cli

    result = CliRunner().invoke(cli, ["version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "0.1.0"


def test_console_script_runs():
    result = subprocess.run(["harness", "version"], capture_output=True, text=True)
    assert result.returncode == 0
    assert result.stdout.strip() == "0.1.0"


def test_tdd_command():
    from harness.cli import cli

    result = CliRunner().invoke(cli, ["tdd"])
    assert result.exit_code == 0
