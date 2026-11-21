"""Tests for the harness docker module."""

import pytest


def test_missing_container_aborts(tmp_path, monkeypatch):
    from harness.docker import run

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text("#!/bin/sh\nexit 1\n")
    docker.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))

    with pytest.raises(SystemExit) as exit_info:
        run("repo_dev", ["make", "tests"], tmp_path)

    assert exit_info.value.code == 1
