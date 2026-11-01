"""High-level tests for the harness public CLI."""

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


def test_tdd_command_is_public():
    from harness.cli import cli

    result = CliRunner().invoke(cli, ["tdd", "--help"])
    assert result.exit_code == 0
    assert "tdd" in result.output.lower()


def test_tdd_requires_a_conforming_repository(tmp_path, monkeypatch):
    from harness.cli import cli

    subprocess.run(["git", "init", "--quiet"], cwd=tmp_path, check=True)
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["tdd"])

    assert result.exit_code != 0
    assert "specs" in result.output.lower()
