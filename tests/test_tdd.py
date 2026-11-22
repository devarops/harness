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


def test_tdd_aborts_when_acceptance_changes_nothing(tmp_path, monkeypatch):
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
    pi.write_text("#!/bin/sh\nprintf 'Nothing to report.'\n")
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
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    monkeypatch.chdir(target)

    with pytest.raises(SystemExit) as exit_info:
        tdd()

    assert exit_info.value.code == 1


def test_tdd_ends_on_completion_without_an_edit(tmp_path, monkeypatch):
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
    pi.write_text("#!/bin/sh\nprintf '<promise>COMPLETE</promise>'\n")
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
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    monkeypatch.chdir(target)

    try:
        tdd()
    except SystemExit:
        exited = True
    else:
        exited = False

    assert exited is False


def test_tdd_aborts_when_acceptance_changes_another_file(tmp_path, monkeypatch):
    from harness.tdd import tdd

    target = tmp_path / "target"
    (target / "specs").mkdir(parents=True)
    (target / "specs" / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\nskip = "reason"\n\n'
        '[criteria.verify]\nrun = "true"\n'
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
        "{\"spec\": \"alpha\", \"criteria\": [{\"description\": \"A\", \"result\": \"failed\"}]}"
        "]}'\n"
        "    exit 1\n"
        "  fi\n"
        "done\n"
        "exit 0\n"
    )
    docker.chmod(0o755)
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        "sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        'printf "more\\n" >> AGENTS.md\n'
    )
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
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    monkeypatch.chdir(target)

    with pytest.raises(SystemExit) as exit_info:
        tdd()

    assert exit_info.value.code == 1


def test_tdd_aborts_when_the_change_is_not_a_spec(tmp_path, monkeypatch):
    from harness.tdd import tdd

    target = tmp_path / "target"
    (target / "specs").mkdir(parents=True)
    (target / "specs" / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\nskip = "reason"\n\n'
        '[criteria.verify]\nrun = "true"\n'
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
        "{\"spec\": \"alpha\", \"criteria\": [{\"description\": \"A\", \"result\": \"failed\"}]}"
        "]}'\n"
        "    exit 1\n"
        "  fi\n"
        "done\n"
        "exit 0\n"
    )
    docker.chmod(0o755)
    pi = bin_dir / "pi"
    pi.write_text('#!/bin/sh\nprintf "more\\n" >> AGENTS.md\n')
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
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    monkeypatch.chdir(target)

    with pytest.raises(SystemExit) as exit_info:
        tdd()

    assert exit_info.value.code == 1


def test_tdd_aborts_when_the_spec_change_is_not_a_removed_line(tmp_path, monkeypatch):
    from harness.tdd import tdd

    target = tmp_path / "target"
    (target / "specs").mkdir(parents=True)
    (target / "specs" / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\nskip = "reason"\n\n'
        '[criteria.verify]\nrun = "true"\n'
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
        "{\"spec\": \"alpha\", \"criteria\": [{\"description\": \"A\", \"result\": \"failed\"}]}"
        "]}'\n"
        "    exit 1\n"
        "  fi\n"
        "done\n"
        "exit 0\n"
    )
    docker.chmod(0o755)
    pi = bin_dir / "pi"
    pi.write_text('#!/bin/sh\nprintf "# note\\n" >> specs/alpha.spec.toml\n')
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
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    monkeypatch.chdir(target)

    with pytest.raises(SystemExit) as exit_info:
        tdd()

    assert exit_info.value.code == 1


def test_tdd_aborts_when_the_removed_line_is_not_a_skip(tmp_path, monkeypatch):
    from harness.tdd import tdd

    target = tmp_path / "target"
    (target / "specs").mkdir(parents=True)
    (target / "specs" / "alpha.spec.toml").write_text(
        '# note\n'
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\nskip = "reason"\n\n'
        '[criteria.verify]\nrun = "true"\n'
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
        "{\"spec\": \"alpha\", \"criteria\": [{\"description\": \"A\", \"result\": \"failed\"}]}"
        "]}'\n"
        "    exit 1\n"
        "  fi\n"
        "done\n"
        "exit 0\n"
    )
    docker.chmod(0o755)
    pi = bin_dir / "pi"
    pi.write_text("#!/bin/sh\nsed -i '/^# note/d' specs/alpha.spec.toml\n")
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
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    monkeypatch.chdir(target)

    with pytest.raises(SystemExit) as exit_info:
        tdd()

    assert exit_info.value.code == 1


def test_tdd_commits_the_activation(tmp_path, monkeypatch):
    from harness.tdd import tdd

    target = tmp_path / "target"
    (target / "specs").mkdir(parents=True)
    (target / "specs" / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\nskip = "reason"\n\n'
        '[criteria.verify]\nrun = "true"\n'
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
        "{\"spec\": \"alpha\", \"criteria\": [{\"description\": \"A\", \"result\": \"failed\"}]}"
        "]}'\n"
        "    exit 1\n"
        "  fi\n"
        "done\n"
        "exit 0\n"
    )
    docker.chmod(0o755)
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        "sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "printf 'Activated A.'\n"
    )
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
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    monkeypatch.chdir(target)

    tdd()

    subject = subprocess.run(
        ["git", "log", "-1", "--format=%s"], cwd=target, capture_output=True, text=True
    ).stdout.strip()
    assert subject == "🔧 Activate the A acceptance criterion"


def test_tdd_commits_the_criterion_whose_skip_left(tmp_path, monkeypatch):
    from harness.tdd import tdd

    target = tmp_path / "target"
    (target / "specs").mkdir(parents=True)
    (target / "specs" / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\n\n[criteria.verify]\nrun = "true"\n\n'
        '[[criteria]]\ndescription = "B"\nskip = "reason"\n\n'
        '[criteria.verify]\nrun = "true"\n'
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
        "{\"spec\": \"alpha\", \"criteria\": ["
        "{\"description\": \"A\", \"result\": \"passed\"}, "
        "{\"description\": \"B\", \"result\": \"failed\"}]}"
        "]}'\n"
        "    exit 1\n"
        "  fi\n"
        "done\n"
        "exit 0\n"
    )
    docker.chmod(0o755)
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        "sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "printf 'Activated B.'\n"
    )
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
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    monkeypatch.chdir(target)

    tdd()

    subject = subprocess.run(
        ["git", "log", "-1", "--format=%s"], cwd=target, capture_output=True, text=True
    ).stdout.strip()
    assert subject == "🔧 Activate the B acceptance criterion"


def test_tdd_puts_the_report_in_the_activation_body(tmp_path, monkeypatch):
    from harness.tdd import tdd

    target = tmp_path / "target"
    (target / "specs").mkdir(parents=True)
    (target / "specs" / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\nskip = "reason"\n\n'
        '[criteria.verify]\nrun = "true"\n'
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
        "{\"spec\": \"alpha\", \"criteria\": [{\"description\": \"A\", \"result\": \"failed\"}]}"
        "]}'\n"
        "    exit 1\n"
        "  fi\n"
        "done\n"
        "exit 0\n"
    )
    docker.chmod(0o755)
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        "sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "printf 'Activated A with low risk.'\n"
    )
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
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    monkeypatch.chdir(target)

    tdd()

    message = subprocess.run(
        ["git", "log", "-1", "--format=%B"], cwd=target, capture_output=True, text=True
    ).stdout
    assert message.split("\n\n", 1)[1].strip() == "Activated A with low risk."


def test_tdd_runs_the_acceptance_red_after_the_commit(tmp_path, monkeypatch):
    from harness.tdd import tdd

    target = tmp_path / "target"
    (target / "specs").mkdir(parents=True)
    (target / "specs" / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\nskip = "reason"\n\n'
        '[criteria.verify]\nrun = "true"\n'
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
        "{\"spec\": \"alpha\", \"criteria\": [{\"description\": \"A\", \"result\": \"failed\"}]}"
        "]}'\n"
        "    exit 1\n"
        "  fi\n"
        "done\n"
        "exit 0\n"
    )
    docker.chmod(0o755)
    log = tmp_path / "pi.log"
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        'case "$*" in\n'
        '  *"acceptance-test Red phase"*) echo atdd-red ;;\n'
        '  *"acceptance phase of the ATDD outer loop"*) echo acceptance ;;\n'
        '  *"Fail sub-phase"*) echo afk-fail ;;\n'
        '  *"Refactor phase"*) echo afk-refactor ;;\n'
        '  *"Green phase"*) echo afk-green ;;\n'
        '  *"Red phase of Test-Driven Development"*) echo afk-red ;;\n'
        '  *) echo unknown ;;\n'
        f'esac >> "{log}"\n'
        "sed -i '/^skip = /d' specs/alpha.spec.toml 2>/dev/null\n"
        "printf 'Activated A.'\n"
    )
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
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    monkeypatch.chdir(target)

    tdd()

    assert log.read_text().splitlines()[:2] == ["acceptance", "atdd-red"]


def test_tdd_aborts_when_the_unit_suite_fails(tmp_path, monkeypatch):
    from harness.tdd import tdd

    target = tmp_path / "target"
    (target / "specs").mkdir(parents=True)
    (target / "specs" / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\nskip = "reason"\n\n'
        '[criteria.verify]\nrun = "true"\n'
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
        "{\"spec\": \"alpha\", \"criteria\": [{\"description\": \"A\", \"result\": \"failed\"}]}"
        "]}'\n"
        "    exit 1\n"
        "  fi\n"
        '  if [ "$arg" = "tests" ]; then\n'
        "    exit 1\n"
        "  fi\n"
        "done\n"
        "exit 0\n"
    )
    docker.chmod(0o755)
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        "sed -i '/^skip = /d' specs/alpha.spec.toml 2>/dev/null\n"
        "printf 'Activated A.'\n"
    )
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
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    monkeypatch.chdir(target)

    with pytest.raises(SystemExit) as exit_info:
        tdd()

    assert exit_info.value.code == 1


def test_tdd_starts_the_unit_red_when_verify_fails(tmp_path, monkeypatch):
    from harness.tdd import tdd

    target = tmp_path / "target"
    (target / "specs").mkdir(parents=True)
    (target / "specs" / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\nskip = "reason"\n\n'
        '[criteria.verify]\nrun = "true"\n'
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
        "{\"spec\": \"alpha\", \"criteria\": [{\"description\": \"A\", \"result\": \"failed\"}]}"
        "]}'\n"
        "    exit 1\n"
        "  fi\n"
        '  if [ "$arg" = "verify" ]; then\n'
        "    exit 1\n"
        "  fi\n"
        "done\n"
        "exit 0\n"
    )
    docker.chmod(0o755)
    log = tmp_path / "pi.log"
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        'case "$*" in\n'
        '  *"acceptance-test Red phase"*) echo atdd-red ;;\n'
        '  *"acceptance phase of the ATDD outer loop"*) echo acceptance ;;\n'
        '  *"Fail sub-phase"*) echo afk-fail ;;\n'
        '  *"Refactor phase"*) echo afk-refactor ;;\n'
        '  *"Green phase"*) echo afk-green ;;\n'
        '  *"Red phase of Test-Driven Development"*) echo afk-red ;;\n'
        '  *) echo unknown ;;\n'
        f'esac >> "{log}"\n'
        "sed -i '/^skip = /d' specs/alpha.spec.toml 2>/dev/null\n"
        "printf 'Activated A.'\n"
    )
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
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    monkeypatch.chdir(target)

    tdd()

    assert log.read_text().splitlines()[:3] == [
        "acceptance",
        "atdd-red",
        "afk-red",
    ]


def test_tdd_runs_the_unit_fail_after_the_unit_red(tmp_path, monkeypatch):
    from harness.tdd import tdd

    target = tmp_path / "target"
    (target / "specs").mkdir(parents=True)
    (target / "specs" / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\nskip = "reason"\n\n'
        '[criteria.verify]\nrun = "true"\n'
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
        "{\"spec\": \"alpha\", \"criteria\": [{\"description\": \"A\", \"result\": \"failed\"}]}"
        "]}'\n"
        "    exit 1\n"
        "  fi\n"
        '  if [ "$arg" = "verify" ]; then\n'
        "    exit 1\n"
        "  fi\n"
        "done\n"
        "exit 0\n"
    )
    docker.chmod(0o755)
    log = tmp_path / "pi.log"
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        'case "$*" in\n'
        '  *"acceptance-test Red phase"*) echo atdd-red ;;\n'
        '  *"acceptance phase of the ATDD outer loop"*) echo acceptance ;;\n'
        '  *"Fail sub-phase"*) echo afk-fail ;;\n'
        '  *"Refactor phase"*) echo afk-refactor ;;\n'
        '  *"Green phase"*) echo afk-green ;;\n'
        '  *"Red phase of Test-Driven Development"*) echo afk-red ;;\n'
        '  *) echo unknown ;;\n'
        f'esac >> "{log}"\n'
        "sed -i '/^skip = /d' specs/alpha.spec.toml 2>/dev/null\n"
        "printf 'Activated A.'\n"
    )
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
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    monkeypatch.chdir(target)

    tdd()

    assert log.read_text().splitlines()[:4] == [
        "acceptance",
        "atdd-red",
        "afk-red",
        "afk-fail",
    ]
