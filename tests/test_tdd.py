"""Tests for the harness TDD loop."""

import os
import subprocess

import pytest


def test_tdd_rejects_a_target_that_does_not_ignore_the_log(tmp_path, monkeypatch):
    from harness.tdd import tdd

    (tmp_path / "specs").mkdir()
    (tmp_path / "specs" / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\n\n[criteria.verify]\nrun = "true"\n'
    )
    (tmp_path / "AGENTS.md").write_text("## Public interface\n\nharness tdd\n")
    (tmp_path / ".gitignore").write_text("__pycache__/\n")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name in ("docker", "pi"):
        script = bin_dir / name
        script.write_text("#!/bin/sh\nexit 0\n")
        script.chmod(0o755)
    monkeypatch.setenv("GIT_AUTHOR_NAME", "Harness")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "harness@example.com")
    monkeypatch.setenv("GIT_COMMITTER_NAME", "Harness")
    monkeypatch.setenv("GIT_COMMITTER_EMAIL", "harness@example.com")
    subprocess.run(["git", "init", "--quiet"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "--all"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "--quiet", "-m", "Target"], cwd=tmp_path, check=True
    )
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit) as exit_info:
        tdd()

    assert exit_info.value.code == 1


def test_tdd_aborts_when_two_criteria_fail(tmp_path, monkeypatch):
    from harness.tdd import tdd

    (tmp_path / "specs").mkdir()
    for name in ("alpha", "beta"):
        (tmp_path / "specs" / f"{name}.spec.toml").write_text(
            f'name = "{name}"\n\n'
            '[[criteria]]\ndescription = "A"\n\n[criteria.verify]\nrun = "true"\n'
        )
    (tmp_path / "AGENTS.md").write_text("## Public interface\n\nharness tdd\n")
    (tmp_path / ".gitignore").write_text("harness.log\n")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "inspect" ]; then\n'
        "  exit 0\n"
        "fi\n"
        'for arg in "$@"; do\n'
        '  if [ "$arg" = "qed" ]; then\n'
        "    printf '%s' '{\"specs\": ["
        "{\"spec\": \"alpha\", \"criteria\": [{\"description\": \"A\", \"result\": \"failed\"}]}, "
        "{\"spec\": \"beta\", \"criteria\": [{\"description\": \"A\", \"result\": \"failed\"}]}"
        "]}'\n"
        "    exit 1\n"
        "  fi\n"
        "done\n"
        "exit 0\n"
    )
    docker.chmod(0o755)
    pi = bin_dir / "pi"
    pi.write_text("#!/bin/sh\nprintf 'Both criteria fail.'\n")
    pi.chmod(0o755)
    monkeypatch.setenv("GIT_AUTHOR_NAME", "Harness")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "harness@example.com")
    monkeypatch.setenv("GIT_COMMITTER_NAME", "Harness")
    monkeypatch.setenv("GIT_COMMITTER_EMAIL", "harness@example.com")
    subprocess.run(["git", "init", "--quiet"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "--all"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "--quiet", "-m", "Target"], cwd=tmp_path, check=True
    )
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit) as exit_info:
        tdd()

    assert exit_info.value.code == 1



def test_tdd_aborts_on_a_dirty_tree(tmp_path, monkeypatch):
    from harness.tdd import tdd

    target = tmp_path / "target"
    (target / "specs").mkdir(parents=True)
    (target / "specs" / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\n\n[criteria.verify]\nrun = "true"\n'
    )
    (target / "AGENTS.md").write_text("## Public interface\n\nharness tdd\n")
    (target / ".gitignore").write_text("harness.log\n")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "inspect" ]; then\n'
        "  exit 0\n"
        "fi\n"
        'for arg in "$@"; do\n'
        '  if [ "$arg" = "qed" ]; then\n'
        "    printf '%s' '{\"specs\": ["
        "{\"spec\": \"alpha\", \"criteria\": [{\"description\": \"A\", \"result\": \"passed\"}]}"
        "]}'\n"
        "    exit 0\n"
        "  fi\n"
        "done\n"
        "exit 0\n"
    )
    docker.chmod(0o755)
    pi = bin_dir / "pi"
    pi.write_text("#!/bin/sh\nexit 0\n")
    pi.chmod(0o755)
    monkeypatch.setenv("GIT_AUTHOR_NAME", "Harness")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "harness@example.com")
    monkeypatch.setenv("GIT_COMMITTER_NAME", "Harness")
    monkeypatch.setenv("GIT_COMMITTER_EMAIL", "harness@example.com")
    subprocess.run(["git", "init", "--quiet"], cwd=target, check=True)
    subprocess.run(["git", "add", "--all"], cwd=target, check=True)
    subprocess.run(
        ["git", "commit", "--quiet", "-m", "Target"], cwd=target, check=True
    )
    (target / "AGENTS.md").write_text("## Public interface\n\nharness tdd, changed\n")
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    monkeypatch.chdir(target)

    with pytest.raises(SystemExit) as exit_info:
        tdd()

    assert exit_info.value.code == 1
