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


def test_command_result_is_returned(tmp_path, monkeypatch):
    from harness.docker import run

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "inspect" ]; then\n'
        "  exit 0\n"
        "fi\n"
        'if [ "$1" = "exec" ] && [ "$2" = "--workdir" ] && '
        f'[ "$3" = "{tmp_path}" ] && '
        '[ "$4" = "repo_dev" ] && [ "$5" = "make" ] && [ "$6" = "tests" ]; then\n'
        "  printf 'ok'\n"
        "  exit 3\n"
        "fi\n"
        "exit 99\n"
    )
    docker.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))

    result = run("repo_dev", ["make", "tests"], tmp_path)

    assert (result.stdout, result.returncode) == ("ok", 3)
