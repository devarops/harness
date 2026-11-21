"""Tests for the harness qed module."""

import pytest


def test_configuration_error_aborts(tmp_path, monkeypatch):
    from harness.qed import verify

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n" 'if [ "$1" = "inspect" ]; then\n' "  exit 0\n" "fi\n" "exit 2\n"
    )
    docker.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))

    with pytest.raises(SystemExit) as exit_info:
        verify("repo_dev", tmp_path, [])

    assert exit_info.value.code == 1


def test_unreadable_payload_aborts(tmp_path, monkeypatch):
    from harness.qed import verify

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "inspect" ]; then\n'
        "  exit 0\n"
        "fi\n"
        "printf 'not json'\n"
        "exit 1\n"
    )
    docker.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))

    with pytest.raises(ValueError):
        verify("repo_dev", tmp_path, [])


def test_payload_without_specs_aborts(tmp_path, monkeypatch):
    from harness.qed import verify

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "inspect" ]; then\n'
        "  exit 0\n"
        "fi\n"
        "printf '%s' '{\"passed\": false}'\n"
        "exit 1\n"
    )
    docker.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))

    with pytest.raises(ValueError):
        verify("repo_dev", tmp_path, [])
