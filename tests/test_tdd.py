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
        "if grep -q '^skip = ' specs/alpha.spec.toml; then\n"
        "  sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "  printf 'Activated A.'\n"
        "else\n"
        "  printf '<promise>COMPLETE</promise>'\n"
        "fi\n"
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
        "if grep -q '^skip = ' specs/alpha.spec.toml; then\n"
        "  sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "  printf 'Activated B.'\n"
        "else\n"
        "  printf '<promise>COMPLETE</promise>'\n"
        "fi\n"
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
        "if grep -q '^skip = ' specs/alpha.spec.toml; then\n"
        "  sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "  printf 'Activated A with low risk.'\n"
        "else\n"
        "  printf '<promise>COMPLETE</promise>'\n"
        "fi\n"
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
        '  *"We are now in the Refactor phase"*) echo afk-refactor ;;\n'
        '  *"We are now in the Green phase"*) echo afk-green ;;\n'
        '  *"Red phase of Test-Driven Development"*) echo afk-red ;;\n'
        '  *) echo unknown ;;\n'
        f'esac >> "{log}"\n'
        "if grep -q '^skip = ' specs/alpha.spec.toml; then\n"
        "  sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "  printf 'Activated A.'\n"
        "else\n"
        "  printf '<promise>COMPLETE</promise>'\n"
        "fi\n"
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
        "if grep -q '^skip = ' specs/alpha.spec.toml; then\n"
        "  sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "  printf 'Activated A.'\n"
        "else\n"
        "  printf '<promise>COMPLETE</promise>'\n"
        "fi\n"
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
    verifications = tmp_path / "verifications"
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
        f'    n=$(cat "{verifications}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{verifications}"\n'
        '    if [ "$n" -eq 2 ]; then exit 1; fi\n'
        "    exit 0\n"
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
        '  *"We are now in the Refactor phase"*) echo afk-refactor ;;\n'
        '  *"We are now in the Green phase"*) echo afk-green ;;\n'
        '  *"Red phase of Test-Driven Development"*) echo afk-red ;;\n'
        '  *) echo unknown ;;\n'
        f'esac >> "{log}"\n'
        "if grep -q '^skip = ' specs/alpha.spec.toml; then\n"
        "  sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "  printf 'Activated A.'\n"
        "else\n"
        "  printf '<promise>COMPLETE</promise>'\n"
        "fi\n"
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
    verifications = tmp_path / "verifications"
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
        f'    n=$(cat "{verifications}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{verifications}"\n'
        '    if [ "$n" -eq 2 ]; then exit 1; fi\n'
        "    exit 0\n"
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
        '  *"We are now in the Refactor phase"*) echo afk-refactor ;;\n'
        '  *"We are now in the Green phase"*) echo afk-green ;;\n'
        '  *"Red phase of Test-Driven Development"*) echo afk-red ;;\n'
        '  *) echo unknown ;;\n'
        f'esac >> "{log}"\n'
        "if grep -q '^skip = ' specs/alpha.spec.toml; then\n"
        "  sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "  printf 'Activated A.'\n"
        "else\n"
        "  printf '<promise>COMPLETE</promise>'\n"
        "fi\n"
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


def test_tdd_runs_the_unit_green_after_the_unit_fail(tmp_path, monkeypatch):
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
    verifications = tmp_path / "verifications"
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
        f'    n=$(cat "{verifications}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{verifications}"\n'
        '    if [ "$n" -eq 2 ]; then exit 1; fi\n'
        "    exit 0\n"
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
        '  *"We are now in the Refactor phase"*) echo afk-refactor ;;\n'
        '  *"We are now in the Green phase"*) echo afk-green ;;\n'
        '  *"Red phase of Test-Driven Development"*) echo afk-red ;;\n'
        '  *) echo unknown ;;\n'
        f'esac >> "{log}"\n'
        "if grep -q '^skip = ' specs/alpha.spec.toml; then\n"
        "  sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "  printf 'Activated A.'\n"
        "else\n"
        "  printf '<promise>COMPLETE</promise>'\n"
        "fi\n"
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

    assert log.read_text().splitlines()[:5] == [
        "acceptance",
        "atdd-red",
        "afk-red",
        "afk-fail",
        "afk-green",
    ]


def test_tdd_runs_the_refactor_after_the_unit_green(tmp_path, monkeypatch):
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
    verifications = tmp_path / "verifications"
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
        f'    n=$(cat "{verifications}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{verifications}"\n'
        '    if [ "$n" -eq 2 ]; then exit 1; fi\n'
        "    exit 0\n"
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
        '  *"We are now in the Refactor phase"*) echo afk-refactor ;;\n'
        '  *"We are now in the Green phase"*) echo afk-green ;;\n'
        '  *"Red phase of Test-Driven Development"*) echo afk-red ;;\n'
        '  *) echo unknown ;;\n'
        f'esac >> "{log}"\n'
        "if grep -q '^skip = ' specs/alpha.spec.toml; then\n"
        "  sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "  printf 'Activated A.'\n"
        "else\n"
        "  printf '<promise>COMPLETE</promise>'\n"
        "fi\n"
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

    assert log.read_text().splitlines()[:6] == [
        "acceptance",
        "atdd-red",
        "afk-red",
        "afk-fail",
        "afk-green",
        "afk-refactor",
    ]


def test_tdd_aborts_when_the_refactor_leaves_the_tree_dirty(tmp_path, monkeypatch):
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
    (target / "notes.txt").write_text("start\n")
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
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        'case "$*" in\n'
        '  *"We are now in the Refactor phase"*)\n'
        '    printf "more\\n" >> notes.txt\n'
        "    exit 0 ;;\n"
        "esac\n"
        "if grep -q '^skip = ' specs/alpha.spec.toml; then\n"
        "  sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "  printf 'Activated A.'\n"
        "else\n"
        "  printf '<promise>COMPLETE</promise>'\n"
        "fi\n"
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


def test_tdd_repeats_the_refactor_while_it_commits(tmp_path, monkeypatch):
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
    (target / "notes.txt").write_text("start\n")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    verifications = tmp_path / "verifications"
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
        f'    n=$(cat "{verifications}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{verifications}"\n'
        '    if [ "$n" -eq 2 ]; then exit 1; fi\n'
        "    exit 0\n"
        "  fi\n"
        "done\n"
        "exit 0\n"
    )
    docker.chmod(0o755)
    log = tmp_path / "pi.log"
    marker = tmp_path / "refactored"
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        'case "$*" in\n'
        '  *"We are now in the Refactor phase"*)\n'
        f'    echo afk-refactor >> "{log}"\n'
        f'    if [ -f "{marker}" ]; then exit 0; fi\n'
        '    printf "more\\n" >> notes.txt\n'
        "    git add notes.txt\n"
        '    git commit -m "Refactor notes" >/dev/null\n'
        f'    touch "{marker}"\n'
        "    exit 0 ;;\n"
        '  *"acceptance-test Red phase"*) echo atdd-red ;;\n'
        '  *"acceptance phase of the ATDD outer loop"*) echo acceptance ;;\n'
        '  *"Fail sub-phase"*) echo afk-fail ;;\n'
        '  *"We are now in the Green phase"*) echo afk-green ;;\n'
        '  *"Red phase of Test-Driven Development"*) echo afk-red ;;\n'
        '  *) echo unknown ;;\n'
        f'esac >> "{log}"\n'
        "if grep -q '^skip = ' specs/alpha.spec.toml; then\n"
        "  sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "  printf 'Activated A.'\n"
        "else\n"
        "  printf '<promise>COMPLETE</promise>'\n"
        "fi\n"
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

    assert log.read_text().splitlines().count("afk-refactor") == 2


def test_tdd_stops_the_refactor_at_the_pass_limit(tmp_path, monkeypatch):
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
    (target / "notes.txt").write_text("start\n")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    verifications = tmp_path / "verifications"
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
        f'    n=$(cat "{verifications}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{verifications}"\n'
        '    if [ "$n" -eq 2 ]; then exit 1; fi\n'
        "    exit 0\n"
        "  fi\n"
        "done\n"
        "exit 0\n"
    )
    docker.chmod(0o755)
    log = tmp_path / "pi.log"
    counter = tmp_path / "runs"
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        'case "$*" in\n'
        '  *"We are now in the Refactor phase"*)\n'
        f'    echo afk-refactor >> "{log}"\n'
        f'    n=$(cat "{counter}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{counter}"\n'
        '    if [ "$n" -gt 12 ]; then exit 0; fi\n'
        '    printf "more\\n" >> notes.txt\n'
        "    git add notes.txt\n"
        '    git commit -m "Refactor notes" >/dev/null\n'
        "    exit 0 ;;\n"
        '  *"acceptance-test Red phase"*) echo atdd-red ;;\n'
        '  *"acceptance phase of the ATDD outer loop"*) echo acceptance ;;\n'
        '  *"Fail sub-phase"*) echo afk-fail ;;\n'
        '  *"We are now in the Green phase"*) echo afk-green ;;\n'
        '  *"Red phase of Test-Driven Development"*) echo afk-red ;;\n'
        '  *) echo unknown ;;\n'
        f'esac >> "{log}"\n'
        "if grep -q '^skip = ' specs/alpha.spec.toml; then\n"
        "  sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "  printf 'Activated A.'\n"
        "else\n"
        "  printf '<promise>COMPLETE</promise>'\n"
        "fi\n"
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

    assert log.read_text().splitlines().count("afk-refactor") == 10


def test_tdd_stops_at_the_pass_limit(tmp_path, monkeypatch):
    from harness.tdd import tdd

    target = tmp_path / "target"
    (target / "specs").mkdir(parents=True)
    (target / "specs" / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\nskip = "first"\n\n'
        '[criteria.verify]\nrun = "true"\n\n'
        '[[criteria]]\ndescription = "B"\nskip = "second"\n\n'
        '[criteria.verify]\nrun = "true"\n\n'
        '[[criteria]]\ndescription = "C"\nskip = "third"\n\n'
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
        "    printf '%s' '{\"specs\": [{\"spec\": \"alpha\", \"criteria\": ["
        "{\"description\": \"A\", \"result\": \"passed\"}, "
        "{\"description\": \"B\", \"result\": \"passed\"}, "
        "{\"description\": \"C\", \"result\": \"passed\"}]}]}'\n"
        "    exit 0\n"
        "  fi\n"
        '  if [ "$arg" = "verify" ]; then\n'
        "    exit 1\n"
        "  fi\n"
        "done\n"
        "exit 0\n"
    )
    docker.chmod(0o755)
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        'case "$*" in\n'
        '  *"acceptance phase of the ATDD outer loop"*)\n'
        "    python3 - <<'EOP'\n"
        "from pathlib import Path\n"
        "path = Path('specs/alpha.spec.toml')\n"
        "lines = path.read_text().splitlines(keepends=True)\n"
        "for index, line in enumerate(lines):\n"
        "    if line.startswith('skip = '):\n"
        "        del lines[index]\n"
        "        path.write_text(''.join(lines))\n"
        "        raise SystemExit(0)\n"
        "raise SystemExit(1)\n"
        "EOP\n"
        '    if [ "$?" = "0" ]; then printf "Activated."; else printf "<promise>COMPLETE</promise>"; fi\n'
        "    exit 0 ;;\n"
        "esac\n"
        "exit 0\n"
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
        tdd(max_passes=2)

    assert exit_info.value.code == 1


def test_tdd_aborts_when_green_commits_a_test(tmp_path, monkeypatch):
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
    (target / "tests").mkdir()
    (target / "tests" / "test_alpha.py").write_text("def test_alpha():\n    pass\n")
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
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        'case "$*" in\n'
        '  *"We are now in the Green phase"*)\n'
        '    printf "def test_more():\\n    pass\\n" >> tests/test_alpha.py\n'
        "    git add tests/test_alpha.py\n"
        '    git commit -m "Green" >/dev/null\n'
        "    exit 0 ;;\n"
        "esac\n"
        "if grep -q '^skip = ' specs/alpha.spec.toml; then\n"
        "  sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "  printf 'Activated A.'\n"
        "else\n"
        "  printf '<promise>COMPLETE</promise>'\n"
        "fi\n"
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


def test_tdd_aborts_when_the_unit_red_changes_production(tmp_path, monkeypatch):
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
    (target / "notes.txt").write_text("start\n")
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
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        'case "$*" in\n'
        '  *"We are now in the Red phase of Test-Driven Development"*)\n'
        '    printf "more\\n" >> notes.txt\n'
        "    exit 0 ;;\n"
        '  *"Fail sub-phase"*)\n'
        "    git add notes.txt\n"
        '    git commit -m "Fail" >/dev/null\n'
        "    exit 0 ;;\n"
        "esac\n"
        "if grep -q '^skip = ' specs/alpha.spec.toml; then\n"
        "  sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "  printf 'Activated A.'\n"
        "else\n"
        "  printf '<promise>COMPLETE</promise>'\n"
        "fi\n"
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


def test_tdd_aborts_when_the_unit_fail_commits_production(tmp_path, monkeypatch):
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
    (target / "notes.txt").write_text("start\n")
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
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        'case "$*" in\n'
        '  *"We are now in the Fail sub-phase"*)\n'
        '    printf "more\\n" >> notes.txt\n'
        "    git add notes.txt\n"
        '    git commit -m "Fail" >/dev/null\n'
        "    exit 0 ;;\n"
        "esac\n"
        "if grep -q '^skip = ' specs/alpha.spec.toml; then\n"
        "  sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "  printf 'Activated A.'\n"
        "else\n"
        "  printf '<promise>COMPLETE</promise>'\n"
        "fi\n"
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


def test_tdd_aborts_when_the_refactor_commits_a_fixture(tmp_path, monkeypatch):
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
    (target / "tests" / "data").mkdir(parents=True)
    (target / "tests" / "data" / "sample.txt").write_text("start\n")
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
    marker = tmp_path / "refactored"
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        'case "$*" in\n'
        '  *"We are now in the Refactor phase"*)\n'
        f'    if [ -f "{marker}" ]; then exit 0; fi\n'
        '    printf "more\\n" >> tests/data/sample.txt\n'
        "    git add tests/data/sample.txt\n"
        '    git commit -m "Refactor" >/dev/null\n'
        f'    touch "{marker}"\n'
        "    exit 0 ;;\n"
        "esac\n"
        "if grep -q '^skip = ' specs/alpha.spec.toml; then\n"
        "  sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "  printf 'Activated A.'\n"
        "else\n"
        "  printf '<promise>COMPLETE</promise>'\n"
        "fi\n"
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


def test_tdd_aborts_without_a_public_interface_section(tmp_path, monkeypatch):
    from harness.tdd import tdd

    target = tmp_path / "target"
    (target / "specs").mkdir(parents=True)
    (target / "specs" / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\nskip = "reason"\n\n'
        '[criteria.verify]\nrun = "true"\n'
    )
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
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        "if grep -q '^skip = ' specs/alpha.spec.toml; then\n"
        "  sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "  printf 'Activated A.'\n"
        "else\n"
        "  printf '<promise>COMPLETE</promise>'\n"
        "fi\n"
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


def test_tdd_writes_the_acceptance_header_to_the_log(tmp_path, monkeypatch):
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
    verifications = tmp_path / "verifications"
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
        f'    n=$(cat "{verifications}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{verifications}"\n'
        '    if [ "$n" -eq 2 ]; then exit 1; fi\n'
        "    exit 0\n"
        "  fi\n"
        "done\n"
        "exit 0\n"
    )
    docker.chmod(0o755)
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        "if grep -q '^skip = ' specs/alpha.spec.toml; then\n"
        "  sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "  printf 'Activated A.'\n"
        "else\n"
        "  printf '<promise>COMPLETE</promise>'\n"
        "fi\n"
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

    log = target / "harness.log"
    written = log.read_text() if log.exists() else ""
    assert written.splitlines()[:1] == ["=== Acceptance cycle 1 of 10 ==="]


def test_tdd_writes_the_red_header_to_the_log(tmp_path, monkeypatch):
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
    verifications = tmp_path / "verifications"
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
        f'    n=$(cat "{verifications}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{verifications}"\n'
        '    if [ "$n" -eq 2 ]; then exit 1; fi\n'
        "    exit 0\n"
        "  fi\n"
        "done\n"
        "exit 0\n"
    )
    docker.chmod(0o755)
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        "if grep -q '^skip = ' specs/alpha.spec.toml; then\n"
        "  sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "  printf 'Activated A.'\n"
        "else\n"
        "  printf '<promise>COMPLETE</promise>'\n"
        "fi\n"
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

    log = target / "harness.log"
    written = log.read_text().splitlines() if log.exists() else []
    assert "=== ATDD Red ===" in written


def test_tdd_writes_the_cycle_header_to_the_log(tmp_path, monkeypatch):
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
    verifications = tmp_path / "verifications"
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
        f'    n=$(cat "{verifications}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{verifications}"\n'
        '    if [ "$n" -eq 2 ]; then exit 1; fi\n'
        "    exit 0\n"
        "  fi\n"
        "done\n"
        "exit 0\n"
    )
    docker.chmod(0o755)
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        "if grep -q '^skip = ' specs/alpha.spec.toml; then\n"
        "  sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "  printf 'Activated A.'\n"
        "else\n"
        "  printf '<promise>COMPLETE</promise>'\n"
        "fi\n"
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

    log = target / "harness.log"
    written = log.read_text().splitlines() if log.exists() else []
    assert "--- TDD cycle 1 (ATDD 1/10) ---" in written


def test_tdd_writes_the_unit_red_header_to_the_log(tmp_path, monkeypatch):
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
    verifications = tmp_path / "verifications"
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
        f'    n=$(cat "{verifications}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{verifications}"\n'
        '    if [ "$n" -eq 2 ]; then exit 1; fi\n'
        "    exit 0\n"
        "  fi\n"
        "done\n"
        "exit 0\n"
    )
    docker.chmod(0o755)
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        "if grep -q '^skip = ' specs/alpha.spec.toml; then\n"
        "  sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "  printf 'Activated A.'\n"
        "else\n"
        "  printf '<promise>COMPLETE</promise>'\n"
        "fi\n"
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

    log = target / "harness.log"
    written = log.read_text().splitlines() if log.exists() else []
    assert "--- TDD Red ---" in written


def test_tdd_writes_the_unit_fail_header_to_the_log(tmp_path, monkeypatch):
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
    verifications = tmp_path / "verifications"
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
        f'    n=$(cat "{verifications}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{verifications}"\n'
        '    if [ "$n" -eq 2 ]; then exit 1; fi\n'
        "    exit 0\n"
        "  fi\n"
        "done\n"
        "exit 0\n"
    )
    docker.chmod(0o755)
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        "if grep -q '^skip = ' specs/alpha.spec.toml; then\n"
        "  sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "  printf 'Activated A.'\n"
        "else\n"
        "  printf '<promise>COMPLETE</promise>'\n"
        "fi\n"
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

    log = target / "harness.log"
    written = log.read_text().splitlines() if log.exists() else []
    assert "--- TDD Fail ---" in written


def test_tdd_writes_the_unit_green_header_to_the_log(tmp_path, monkeypatch):
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
    verifications = tmp_path / "verifications"
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
        f'    n=$(cat "{verifications}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{verifications}"\n'
        '    if [ "$n" -eq 2 ]; then exit 1; fi\n'
        "    exit 0\n"
        "  fi\n"
        "done\n"
        "exit 0\n"
    )
    docker.chmod(0o755)
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        "if grep -q '^skip = ' specs/alpha.spec.toml; then\n"
        "  sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "  printf 'Activated A.'\n"
        "else\n"
        "  printf '<promise>COMPLETE</promise>'\n"
        "fi\n"
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

    log = target / "harness.log"
    written = log.read_text().splitlines() if log.exists() else []
    assert "--- TDD Green ---" in written


def test_tdd_writes_the_refactor_header_to_the_log(tmp_path, monkeypatch):
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
    (target / "notes.txt").write_text("start\n")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    verifications = tmp_path / "verifications"
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
        f'    n=$(cat "{verifications}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{verifications}"\n'
        '    if [ "$n" -eq 2 ]; then exit 1; fi\n'
        "    exit 0\n"
        "  fi\n"
        "done\n"
        "exit 0\n"
    )
    docker.chmod(0o755)
    marker = tmp_path / "refactored"
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        'case "$*" in\n'
        '  *"We are now in the Refactor phase"*)\n'
        f'    if [ -f "{marker}" ]; then exit 0; fi\n'
        '    printf "more\\n" >> notes.txt\n'
        "    git add notes.txt\n"
        '    git commit -m "Refactor" >/dev/null\n'
        f'    touch "{marker}"\n'
        "    exit 0 ;;\n"
        "esac\n"
        "if grep -q '^skip = ' specs/alpha.spec.toml; then\n"
        "  sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "  printf 'Activated A.'\n"
        "else\n"
        "  printf '<promise>COMPLETE</promise>'\n"
        "fi\n"
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

    log = target / "harness.log"
    written = log.read_text().splitlines() if log.exists() else []
    assert "--- Refactor 1 of 10 ---" in written


def test_tdd_writes_the_prompt_output_after_its_line(tmp_path, monkeypatch):
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
    verifications = tmp_path / "verifications"
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
        f'    n=$(cat "{verifications}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{verifications}"\n'
        '    if [ "$n" -eq 2 ]; then exit 1; fi\n'
        "    exit 0\n"
        "  fi\n"
        "done\n"
        "exit 0\n"
    )
    docker.chmod(0o755)
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        "if grep -q '^skip = ' specs/alpha.spec.toml; then\n"
        "  sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "  printf 'Activated A.'\n"
        "else\n"
        "  printf '<promise>COMPLETE</promise>'\n"
        "fi\n"
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

    log = target / "harness.log"
    written = log.read_text().splitlines() if log.exists() else []
    header = written.index("=== Acceptance cycle 1 of 10 ===")
    assert written[header + 1 : header + 2] == ["Activated A."]


def test_tdd_passes_the_model_to_the_prompts(tmp_path, monkeypatch):
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
    verifications = tmp_path / "verifications"
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
        f'    n=$(cat "{verifications}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{verifications}"\n'
        '    if [ "$n" -eq 2 ]; then exit 1; fi\n'
        "    exit 0\n"
        "  fi\n"
        "done\n"
        "exit 0\n"
    )
    docker.chmod(0o755)
    args = tmp_path / "args.txt"
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        f'printf \'%s\\n\' "$@" >> "{args}"\n'
        "if grep -q '^skip = ' specs/alpha.spec.toml; then\n"
        "  sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "  printf 'Activated A.'\n"
        "else\n"
        "  printf '<promise>COMPLETE</promise>'\n"
        "fi\n"
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

    tdd(model="deepseek/v4")

    recorded = args.read_text().splitlines()
    assert recorded[:4] == ["--no-session", "--print", "--models", "deepseek/v4"]


def test_tdd_aborts_when_a_prompt_reports_failure(tmp_path, monkeypatch):
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
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        "if grep -q '^skip = ' specs/alpha.spec.toml; then\n"
        "  sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "  printf '<error>FAIL: the criterion is ambiguous</error>'\n"
        "else\n"
        "  printf '<promise>COMPLETE</promise>'\n"
        "fi\n"
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


def test_tdd_aborts_when_the_acceptance_red_commits_production(tmp_path, monkeypatch):
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
    (target / "notes.txt").write_text("start\n")
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
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        'case "$*" in\n'
        '  *"acceptance-test Red phase"*)\n'
        '    printf "more\\n" >> notes.txt\n'
        "    git add notes.txt\n"
        '    git commit -m "Red" >/dev/null\n'
        "    exit 0 ;;\n"
        "esac\n"
        "if grep -q '^skip = ' specs/alpha.spec.toml; then\n"
        "  sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "  printf 'Activated A.'\n"
        "else\n"
        "  printf '<promise>COMPLETE</promise>'\n"
        "fi\n"
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


def test_tdd_runs_container_commands_in_the_workdir(tmp_path, monkeypatch):
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
    calls = tmp_path / "calls.txt"
    verifications = tmp_path / "verifications"
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "inspect" ]; then\n'
        "  exit 0\n"
        "fi\n"
        'if [ "$1" = "exec" ]; then\n'
        f'  printf \'%s \' "$@" >> "{calls}"\n'
        f'  printf \'\\n\' >> "{calls}"\n'
        "fi\n"
        'for arg in "$@"; do\n'
        '  if [ "$arg" = "qed" ]; then\n'
        "    printf '%s' '{\"specs\": ["
        "{\"spec\": \"alpha\", \"criteria\": [{\"description\": \"A\", \"result\": \"failed\"}]}"
        "]}'\n"
        "    exit 1\n"
        "  fi\n"
        '  if [ "$arg" = "verify" ]; then\n'
        f'    n=$(cat "{verifications}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{verifications}"\n'
        '    if [ "$n" -eq 2 ]; then exit 1; fi\n'
        "    exit 0\n"
        "  fi\n"
        "done\n"
        "exit 0\n"
    )
    docker.chmod(0o755)
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        "if grep -q '^skip = ' specs/alpha.spec.toml; then\n"
        "  sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "  printf 'Activated A.'\n"
        "else\n"
        "  printf '<promise>COMPLETE</promise>'\n"
        "fi\n"
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

    recorded = [line.split() for line in calls.read_text().splitlines()]
    workdirs = {parts[2] for parts in recorded if parts[0] == "exec"}
    assert workdirs == {"/workdir"}


def test_tdd_runs_the_inner_cycle_before_acceptance_when_verify_fails(
    tmp_path, monkeypatch
):
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
    verified = tmp_path / "verified"
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
        '  if [ "$arg" = "verify" ]; then\n'
        f'    if [ -f "{verified}" ]; then exit 0; fi\n'
        f'    touch "{verified}"\n'
        "    exit 1\n"
        "  fi\n"
        "done\n"
        "exit 0\n"
    )
    docker.chmod(0o755)
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        'case "$*" in\n'
        '  *"acceptance-test Red phase"*) : ;;\n'
        '  *"acceptance phase of the ATDD outer loop"*)\n'
        "    if grep -q '^skip = ' specs/alpha.spec.toml; then\n"
        "      sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "      printf 'Activated A.'\n"
        "    else\n"
        "      printf '<promise>COMPLETE</promise>'\n"
        "    fi ;;\n"
        '  *"Fail sub-phase"*)\n'
        "    git add tests/test_unit.py\n"
        '    git commit -m "Fail" >/dev/null ;;\n'
        '  *"We are now in the Refactor phase"*) : ;;\n'
        '  *"We are now in the Green phase"*)\n'
        "    printf 'def product():\\n    return 1\\n' > product.py\n"
        "    git add product.py\n"
        '    git commit -m "Green" >/dev/null ;;\n'
        '  *"Red phase of Test-Driven Development"*)\n'
        "    mkdir -p tests\n"
        "    printf 'def test_unit():\\n    pass\\n' > tests/test_unit.py ;;\n"
        "esac\n"
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

    written = (target / "harness.log").read_text().splitlines()
    assert written.index("--- TDD Red ---") < written.index(
        "=== Acceptance cycle 1 of 10 ==="
    )


def test_tdd_checks_verification_after_the_inner_cycle(tmp_path, monkeypatch):
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
    checks = tmp_path / "checks"
    verified = tmp_path / "verified"
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
        '  if [ "$arg" = "verify" ]; then\n'
        f'    n=$(cat "{checks}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{checks}"\n'
        '    if [ "$n" -eq 1 ]; then exit 1; fi\n'
        f'    touch "{verified}"\n'
        "    exit 0\n"
        "  fi\n"
        "done\n"
        "exit 0\n"
    )
    docker.chmod(0o755)
    events = tmp_path / "events"
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        'case "$*" in\n'
        '  *"acceptance-test Red phase"*) : ;;\n'
        '  *"acceptance phase of the ATDD outer loop"*)\n'
        f'    if [ -f "{verified}" ]; then echo "after pass" >> "{events}"; '
        f'else echo "before pass" >> "{events}"; fi\n'
        "    if grep -q '^skip = ' specs/alpha.spec.toml; then\n"
        "      sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "      printf 'Activated A.'\n"
        "    else\n"
        "      printf '<promise>COMPLETE</promise>'\n"
        "    fi ;;\n"
        '  *"Fail sub-phase"*)\n'
        "    git add tests/test_unit.py\n"
        '    git commit -m "Fail" >/dev/null ;;\n'
        '  *"We are now in the Refactor phase"*) : ;;\n'
        '  *"We are now in the Green phase"*)\n'
        "    printf 'def product():\\n    return 1\\n' > product.py\n"
        "    git add product.py\n"
        '    git commit -m "Green" >/dev/null ;;\n'
        '  *"Red phase of Test-Driven Development"*)\n'
        "    mkdir -p tests\n"
        "    printf 'def test_unit():\\n    pass\\n' > tests/test_unit.py ;;\n"
        "esac\n"
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

    assert events.read_text().splitlines()[0] == "after pass"


def test_tdd_repeats_the_inner_cycle_in_the_same_pass(tmp_path, monkeypatch):
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
    checks = tmp_path / "checks"
    reds = tmp_path / "reds"
    greens = tmp_path / "greens"
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
        f'    n=$(cat "{checks}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{checks}"\n'
        '    if [ "$n" -gt 1 ] && [ "$n" -lt 4 ]; then exit 1; fi\n'
        "    exit 0\n"
        "  fi\n"
        "done\n"
        "exit 0\n"
    )
    docker.chmod(0o755)
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        'case "$*" in\n'
        '  *"acceptance-test Red phase"*) : ;;\n'
        '  *"acceptance phase of the ATDD outer loop"*)\n'
        "    if grep -q '^skip = ' specs/alpha.spec.toml; then\n"
        "      sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "      printf 'Activated A.'\n"
        "    else\n"
        "      printf '<promise>COMPLETE</promise>'\n"
        "    fi ;;\n"
        '  *"Fail sub-phase"*)\n'
        "    git add tests/test_unit.py\n"
        '    git commit -m "Fail" >/dev/null ;;\n'
        '  *"We are now in the Refactor phase"*) : ;;\n'
        '  *"We are now in the Green phase"*)\n'
        f'    n=$(cat "{greens}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{greens}"\n'
        "    printf 'def product_%s():\\n    return 1\\n' \"$n\" >> product.py\n"
        "    git add product.py\n"
        '    git commit -m "Green" >/dev/null ;;\n'
        '  *"Red phase of Test-Driven Development"*)\n'
        "    mkdir -p tests\n"
        f'    n=$(cat "{reds}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{reds}"\n'
        "    printf 'def test_unit_%s():\\n    pass\\n' \"$n\" >> tests/test_unit.py ;;\n"
        "esac\n"
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

    written = (target / "harness.log").read_text().splitlines()
    second = written.index("=== Acceptance cycle 2 of 10 ===")
    cycles = [line for line in written[:second] if line.startswith("--- TDD cycle")]
    assert cycles[-1].endswith("(ATDD 1/10)")
