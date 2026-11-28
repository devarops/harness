"""Tests for the harness TDD loop."""

import os
import subprocess
import sys
import time

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


def test_tdd_rejects_a_target_that_does_not_ignore_the_counts(tmp_path, monkeypatch):
    from harness.tdd import tdd

    (tmp_path / "specs").mkdir()
    (tmp_path / "specs" / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\n\n[criteria.verify]\nrun = "true"\n'
    )
    (tmp_path / "AGENTS.md").write_text("## Public interface\n\nharness tdd\n")
    (tmp_path / ".gitignore").write_text("harness.log\n")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text("#!/bin/sh\nexit 0\n")
    docker.chmod(0o755)
    pi = bin_dir / "pi"
    pi.write_text("#!/bin/sh\nprintf '<promise>COMPLETE</promise>'\n")
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


def test_tdd_rejects_a_target_without_the_mutants_target(tmp_path, monkeypatch):
    from harness.tdd import tdd

    (tmp_path / "specs").mkdir()
    (tmp_path / "specs" / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\n\n[criteria.verify]\nrun = "true"\n'
    )
    (tmp_path / "AGENTS.md").write_text("## Public interface\n\nharness tdd\n")
    (tmp_path / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "inspect" ]; then exit 0; fi\n'
        'for arg in "$@"; do\n'
        '  if [ "$arg" = "mutants" ]; then exit 1; fi\n'
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


def test_tdd_runs_mutants_before_the_first_pass(tmp_path, monkeypatch):
    from harness.tdd import tdd

    (tmp_path / "specs").mkdir()
    (tmp_path / "specs" / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\nskip = "reason"\n\n'
        '[criteria.verify]\nrun = "true"\n'
    )
    (tmp_path / "AGENTS.md").write_text("## Public interface\n\nharness tdd\n")
    (tmp_path / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    mutants = tmp_path / "mutants"
    prompts = tmp_path / "prompts"
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "inspect" ]; then exit 0; fi\n'
        'case "$*" in\n'
        '  *"--dry-run mutants"*) exit 0 ;;\n'
        "esac\n"
        'for arg in "$@"; do\n'
        '  if [ "$arg" = "mutants" ]; then\n'
        f'    echo mutants >> "{mutants}"\n'
        "    exit 1\n"
        "  fi\n"
        "done\n"
        "exit 0\n"
    )
    docker.chmod(0o755)
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        f'echo prompt >> "{prompts}"\n'
        "printf '<promise>COMPLETE</promise>'\n"
    )
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

    try:
        tdd()
    except SystemExit:
        pass

    assert not (tmp_path / "prompts").exists()


def test_tdd_dry_runs_mutants_with_the_long_option(tmp_path, monkeypatch):
    from harness.tdd import tdd

    (tmp_path / "specs").mkdir()
    (tmp_path / "specs" / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\nskip = "reason"\n\n'
        '[criteria.verify]\nrun = "true"\n'
    )
    (tmp_path / "AGENTS.md").write_text("## Public interface\n\nharness tdd\n")
    (tmp_path / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\ncalls\n"
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    calls = tmp_path / "calls"
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        f'echo "$*" >> "{calls}"\n'
        'if [ "$1" = "inspect" ]; then exit 0; fi\n'
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
    subprocess.run(["git", "init", "--quiet"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "--all"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "--quiet", "-m", "Target"], cwd=tmp_path, check=True
    )
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    monkeypatch.chdir(tmp_path)

    try:
        tdd()
    except SystemExit:
        pass

    assert "--dry-run mutants" in calls.read_text()


def test_tdd_accepts_a_host_without_the_mutation_prompts(tmp_path, monkeypatch):
    import harness.tdd as module

    (tmp_path / "specs").mkdir()
    (tmp_path / "specs" / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\n\n[criteria.verify]\nrun = "true"\n'
    )
    (tmp_path / "AGENTS.md").write_text("## Public interface\n\nharness tdd\n")
    (tmp_path / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "afk-score.md").write_text("Score.")
    (prompts / "atdd-acceptance.md").write_text("Accept.")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text("#!/bin/sh\nexit 0\n")
    docker.chmod(0o755)
    pi = bin_dir / "pi"
    pi.write_text("#!/bin/sh\nprintf '<promise>COMPLETE</promise>'\n")
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
    monkeypatch.setattr(module, "_PROMPT_DIR", prompts)

    try:
        module.tdd()
    except SystemExit as error:
        code = error.code
    else:
        code = None

    assert code is None


def test_tdd_aborts_when_the_startup_verify_fails(tmp_path, monkeypatch):
    from harness.tdd import tdd

    (tmp_path / "specs").mkdir()
    (tmp_path / "specs" / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\n\n[criteria.verify]\nrun = "true"\n'
    )
    (tmp_path / "AGENTS.md").write_text("## Public interface\n\nharness tdd\n")
    (tmp_path / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\nverifications\n"
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    verifications = tmp_path / "verifications"
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "inspect" ]; then exit 0; fi\n'
        'for arg in "$@"; do\n'
        '  if [ "$arg" = "mutants" ]; then exit 0; fi\n'
        '  if [ "$arg" = "verify" ]; then\n'
        f'    n=$(cat "{verifications}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{verifications}"\n'
        '    if [ "$n" -eq 1 ]; then exit 1; fi\n'
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


def test_tdd_rejects_a_host_without_the_score_prompt(tmp_path, monkeypatch):
    import harness.tdd as module

    (tmp_path / "specs").mkdir()
    (tmp_path / "specs" / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\n\n[criteria.verify]\nrun = "true"\n'
    )
    (tmp_path / "AGENTS.md").write_text("## Public interface\n\nharness tdd\n")
    (tmp_path / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "atdd-acceptance.md").write_text("Accept.")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text("#!/bin/sh\nexit 0\n")
    docker.chmod(0o755)
    pi = bin_dir / "pi"
    pi.write_text("#!/bin/sh\nprintf '<promise>COMPLETE</promise>'\n")
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
    monkeypatch.setattr(module, "_PROMPT_DIR", prompts)

    with pytest.raises(SystemExit) as exit_info:
        module.tdd()

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
    (tmp_path / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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


def test_skip_owner_finds_a_criterion_with_a_multiline_description(
    tmp_path, monkeypatch
):
    from harness import spec
    from harness.tdd import _skip_owner

    (tmp_path / "specs").mkdir()
    path = tmp_path / "specs" / "alpha.spec.toml"
    path.write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "First."\n\n'
        '[criteria.verify]\nrun = "true"\n\n'
        '[[criteria]]\ndescription = """\n'
        "When the same context appears more than once, the response equals the\n"
        "response with that context once, because repeated values collapse.\n"
        '"""\nskip = "Not implemented"\n\n'
        '[criteria.verify]\nrun = "true"\n'
    )
    monkeypatch.setenv("GIT_AUTHOR_NAME", "Harness")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "harness@example.com")
    monkeypatch.setenv("GIT_COMMITTER_NAME", "Harness")
    monkeypatch.setenv("GIT_COMMITTER_EMAIL", "harness@example.com")
    subprocess.run(["git", "init", "--quiet"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "--all"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "--quiet", "-m", "Target"], cwd=tmp_path, check=True
    )
    path.write_text(path.read_text().replace('skip = "Not implemented"\n', ""))
    alpha = next(item for item in spec.import_specs(tmp_path) if item.name == "alpha")
    diff = subprocess.run(
        ["git", "diff"], cwd=tmp_path, capture_output=True, text=True
    ).stdout
    removed = [
        line
        for line in diff.splitlines()
        if line.startswith("-") and not line.startswith("---")
    ]

    owner = _skip_owner(alpha, diff, removed[0])

    assert owner.description.startswith("When the same context")


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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    verify_count = tmp_path / "verify-count"
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
        '  if [ "$arg" = "verify" ]; then\n'
        f'    n=$(cat "{verify_count}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{verify_count}"\n'
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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
    scores = tmp_path / "scores"
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        "exec 3>&1\n"
        'case "$*" in\n'
        '  *"We are now in the Refactor phase"*)\n'
        f'    echo afk-refactor >> "{log}"\n'
        f'    if [ -f "{marker}" ]; then exit 0; fi\n'
        '    printf "more\\n" >> notes.txt\n'
        "    git add notes.txt\n"
        '    git commit -m "Refactor notes" >/dev/null\n'
        f'    touch "{marker}"\n'
        "    exit 0 ;;\n"
        '  *"Commit: "*)\n'
        f'    n=$(cat "{scores}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{scores}"\n'
        '    if [ $((n % 6)) -ge 1 ] && [ $((n % 6)) -le 3 ]; then\n'
        "      printf '<score>4</score>' >&3\n"
        "    else\n"
        "      printf '<score>2</score>' >&3\n"
        "    fi\n"
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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
    scores = tmp_path / "scores"
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        "exec 3>&1\n"
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
        '  *"Commit: "*)\n'
        f'    n=$(cat "{scores}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{scores}"\n'
        '    if [ $((n % 6)) -ge 1 ] && [ $((n % 6)) -le 3 ]; then\n'
        "      printf '<score>4</score>' >&3\n"
        "    else\n"
        "      printf '<score>2</score>' >&3\n"
        "    fi\n"
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


def test_tdd_scores_the_refactor_before_and_after(tmp_path, monkeypatch):
    from harness.tdd import _refactor

    target = tmp_path / "target"
    target.mkdir()
    (target / "notes.txt").write_text("start\n")
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    scores = tmp_path / "scores"
    scores.write_text("")
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        'case "$*" in\n'
        '  *"We are now in the Refactor phase"*)\n'
        '    printf "more\\n" >> notes.txt\n'
        "    git add notes.txt\n"
        '    git commit -m "Refactor notes" >/dev/null\n'
        "    exit 0 ;;\n"
        '  *"Commit: "*)\n'
        "    printf '%s' \"$*\" | awk '/^Commit: /{c=$2}"
        " /^notes.txt$/{f=1} END{print c, f+0}' >> \""
        f'{scores}"\n'
        "    printf '<score>1</score>'\n"
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
    old = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=target,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    _refactor(target, 1, None)

    new = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=target,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert scores.read_text().splitlines() == [f"{old} 1"] * 3 + [f"{new} 1"] * 3


def test_tdd_clears_the_count_files_before_scoring(tmp_path, monkeypatch):
    from harness.tdd import _refactor

    target = tmp_path / "target"
    target.mkdir()
    (target / "notes.txt").write_text("start\n")
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
    (target / "score-before.txt").write_text("99\n")
    (target / "score-after.txt").write_text("99\n")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        'case "$*" in\n'
        '  *"We are now in the Refactor phase"*)\n'
        '    printf "more\\n" >> notes.txt\n'
        "    git add notes.txt\n"
        '    git commit -m "Refactor notes" >/dev/null\n'
        "    exit 0 ;;\n"
        '  *"Commit: "*) printf \'<score>7</score>\' ;;\n'
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

    _refactor(target, 1, None)

    before = (target / "score-before.txt").read_text().splitlines()
    after = (target / "score-after.txt").read_text().splitlines()
    assert (before, after) == (["7"] * 3, ["7"] * 3)


def test_tdd_records_both_medians_in_the_log(tmp_path, monkeypatch):
    from harness.tdd import _refactor

    target = tmp_path / "target"
    target.mkdir()
    (target / "notes.txt").write_text("start\n")
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    before = tmp_path / "before"
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        'case "$*" in\n'
        '  *"We are now in the Refactor phase"*)\n'
        '    printf "more\\n" >> notes.txt\n'
        "    git add notes.txt\n"
        '    git commit -m "Refactor notes" >/dev/null\n'
        "    exit 0 ;;\n"
        '  *"Commit: "*)\n'
        f'    if printf \'%s\' "$*" | grep --quiet "Commit: $(cat {before})"; then\n'
        "      printf '<score>4</score>'\n"
        "    else\n"
        "      printf '<score>2</score>'\n"
        "    fi ;;\n"
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
    before.write_text(
        subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=target,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    )

    _refactor(target, 1, None)

    written = (target / "harness.log").read_text().splitlines()
    assert written[-2:] == [
        "--- TDD Median weakness count before 4 ---",
        "--- TDD Median weakness count after 2 ---",
    ]


def test_tdd_resets_a_refactor_that_raises_the_median(tmp_path, monkeypatch):
    from harness.tdd import _refactor

    target = tmp_path / "target"
    target.mkdir()
    (target / "notes.txt").write_text("start\n")
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    before = tmp_path / "before"
    marker = tmp_path / "refactored"
    runs = tmp_path / "runs"
    runs.write_text("")
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        'case "$*" in\n'
        '  *"We are now in the Refactor phase"*)\n'
        f'    echo refactor >> "{runs}"\n'
        f'    if [ -f "{marker}" ]; then exit 0; fi\n'
        f'    touch "{marker}"\n'
        '    printf "more\\n" >> notes.txt\n'
        "    git add notes.txt\n"
        '    git commit -m "Refactor notes" >/dev/null\n'
        "    exit 0 ;;\n"
        '  *"Commit: "*)\n'
        f'    if printf \'%s\' "$*" | grep --quiet "Commit: $(cat {before})"; then\n'
        "      printf '<score>4</score>'\n"
        "    else\n"
        "      printf '<score>9</score>'\n"
        "    fi ;;\n"
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
    old = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=target,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    before.write_text(old)

    _refactor(target, 2, None)

    head = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=target,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    tree = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=target,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert (head, tree, runs.read_text().splitlines()) == (old, "", ["refactor"])


def test_tdd_stops_when_the_median_is_equal(tmp_path, monkeypatch):
    from harness.tdd import _refactor

    target = tmp_path / "target"
    target.mkdir()
    (target / "notes.txt").write_text("start\n")
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    marker = tmp_path / "refactored"
    runs = tmp_path / "runs"
    runs.write_text("")
    new = tmp_path / "new"
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        'case "$*" in\n'
        '  *"We are now in the Refactor phase"*)\n'
        f'    echo refactor >> "{runs}"\n'
        f'    if [ -f "{marker}" ]; then exit 0; fi\n'
        f'    touch "{marker}"\n'
        '    printf "more\\n" >> notes.txt\n'
        "    git add notes.txt\n"
        '    git commit -m "Refactor notes" >/dev/null\n'
        f'    git rev-parse --short HEAD > "{new}"\n'
        "    exit 0 ;;\n"
        '  *"Commit: "*) printf \'<score>4</score>\' ;;\n'
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

    _refactor(target, 2, None)

    head = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=target,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    tree = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=target,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert (head, tree, runs.read_text().splitlines()) == (
        new.read_text().strip(),
        "",
        ["refactor"],
    )


def test_tdd_stops_when_no_valid_score_exists(tmp_path, monkeypatch):
    from harness.tdd import _refactor

    target = tmp_path / "target"
    target.mkdir()
    (target / "notes.txt").write_text("start\n")
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    marker = tmp_path / "refactored"
    runs = tmp_path / "runs"
    runs.write_text("")
    new = tmp_path / "new"
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        'case "$*" in\n'
        '  *"We are now in the Refactor phase"*)\n'
        f'    echo refactor >> "{runs}"\n'
        f'    if [ -f "{marker}" ]; then exit 0; fi\n'
        f'    touch "{marker}"\n'
        '    printf "more\\n" >> notes.txt\n'
        "    git add notes.txt\n"
        '    git commit -m "Refactor notes" >/dev/null\n'
        f'    git rev-parse --short HEAD > "{new}"\n'
        "    exit 0 ;;\n"
        '  *"Commit: "*) printf \'no score\' ;;\n'
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

    _refactor(target, 2, None)

    head = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=target,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    tree = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=target,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert (head, tree, runs.read_text().splitlines()) == (
        new.read_text().strip(),
        "",
        ["refactor"],
    )


def test_tdd_keeps_the_last_refactor_at_the_pass_limit(tmp_path, monkeypatch):
    from harness.tdd import _refactor

    target = tmp_path / "target"
    target.mkdir()
    (target / "notes.txt").write_text("start\n")
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    runs = tmp_path / "runs"
    runs.write_text("")
    scores = tmp_path / "scores"
    last = tmp_path / "last"
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        'case "$*" in\n'
        '  *"We are now in the Refactor phase"*)\n'
        f'    echo refactor >> "{runs}"\n'
        '    printf "more\\n" >> notes.txt\n'
        "    git add notes.txt\n"
        '    git commit -m "Refactor notes" >/dev/null\n'
        f'    git rev-parse --short HEAD > "{last}"\n'
        "    exit 0 ;;\n"
        '  *"Commit: "*)\n'
        f'    n=$(cat "{scores}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{scores}"\n'
        '    if [ $((n % 6)) -ge 1 ] && [ $((n % 6)) -le 3 ]; then\n'
        "      printf '<score>4</score>'\n"
        "    else\n"
        "      printf '<score>2</score>'\n"
        "    fi ;;\n"
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

    _refactor(target, 2, None)

    head = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=target,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    tree = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=target,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert (head, tree, runs.read_text().splitlines()) == (
        last.read_text().strip(),
        "",
        ["refactor", "refactor"],
    )


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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
        "    printf '%s' '{\"specs\": [{\"spec\": \"alpha\", \"criteria\": ["
        "{\"description\": \"A\", \"result\": \"passed\"}, "
        "{\"description\": \"B\", \"result\": \"passed\"}, "
        "{\"description\": \"C\", \"result\": \"passed\"}]}]}'\n"
        "    exit 0\n"
        "  fi\n"
        '  if [ "$arg" = "verify" ]; then\n'
        f'    n=$(cat "{verifications}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{verifications}"\n'
        '    if [ $((n % 2)) -eq 0 ]; then exit 1; fi\n'
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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
    assert "--- TDD Refactor 1 of 10 ---" in written


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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
        '    if [ "$n" -gt 1 ]; then exit 1; fi\n'
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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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


def test_tdd_runs_acceptance_before_the_inner_cycle(
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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    verify_count = tmp_path / "verify-count"
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
        "{\"spec\": \"alpha\", \"criteria\": [{\"description\": \"A\", \"result\": \"failed\"}]}"
        "]}'\n"
        "    exit 0\n"
        "  fi\n"
        '  if [ "$arg" = "verify" ]; then\n'
        f'    n=$(cat "{verify_count}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{verify_count}"\n'
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
    assert written.index("=== Acceptance cycle 1 of 10 ===") < written.index(
        "--- TDD Red ---"
    )


def test_tdd_runs_mutants_after_the_green_commit(tmp_path, monkeypatch):
    from harness.tdd import tdd

    target = tmp_path / "target"
    (target / "specs").mkdir(parents=True)
    (target / "specs" / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\nskip = "reason"\n\n'
        '[criteria.verify]\nrun = "true"\n'
    )
    (target / "AGENTS.md").write_text("## Public interface\n\nharness tdd\n")
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    verify_count = tmp_path / "verify-count"
    mutants = tmp_path / "mutants"
    mutants.write_text("")
    hunts = tmp_path / "hunts"
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "inspect" ]; then\n'
        "  exit 0\n"
        "fi\n"
        'case "$*" in\n'
        '  *"--dry-run mutants"*) exit 0 ;;\n'
        "esac\n"
        'for arg in "$@"; do\n'
        '  if [ "$arg" = "qed" ]; then\n'
        "    printf '%s' '{\"specs\": ["
        "{\"spec\": \"alpha\", \"criteria\": [{\"description\": \"A\", \"result\": \"failed\"}]}"
        "]}'\n"
        "    exit 1\n"
        "  fi\n"
        '  if [ "$arg" = "mutants" ]; then\n'
        f'    echo mutants >> "{mutants}"\n'
        "    exit 0\n"
        "  fi\n"
        '  if [ "$arg" = "verify" ]; then\n'
        f'    n=$(cat "{verify_count}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{verify_count}"\n'
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
        '  *"mutation hunting phase"*) echo kill >> "' + str(hunts) + '" ;;\n'
        '  *"committing the test that kills"*) echo commit >> "' + str(hunts) + '" ;;\n'
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

    assert (mutants.read_text().splitlines(), hunts.exists()) == (
        ["mutants", "mutants"],
        False,
    )


def test_tdd_announces_survivors_without_hunting(tmp_path, monkeypatch):
    from harness.tdd import tdd

    target = tmp_path / "target"
    (target / "specs").mkdir(parents=True)
    (target / "specs" / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\nskip = "reason"\n\n'
        '[criteria.verify]\nrun = "true"\n'
    )
    (target / "AGENTS.md").write_text("## Public interface\n\nharness tdd\n")
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    verify_count = tmp_path / "verify-count"
    mutant_count = tmp_path / "mutant-count"
    hunts = tmp_path / "hunts"
    refactors = tmp_path / "refactors"
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "inspect" ]; then\n'
        "  exit 0\n"
        "fi\n"
        'case "$*" in\n'
        '  *"--dry-run mutants"*) exit 0 ;;\n'
        "esac\n"
        'for arg in "$@"; do\n'
        '  if [ "$arg" = "qed" ]; then\n'
        "    printf '%s' '{\"specs\": ["
        "{\"spec\": \"alpha\", \"criteria\": [{\"description\": \"A\", \"result\": \"failed\"}]}"
        "]}'\n"
        "    exit 1\n"
        "  fi\n"
        '  if [ "$arg" = "mutants" ]; then\n'
        f'    n=$(cat "{mutant_count}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{mutant_count}"\n'
        '    if [ "$n" -eq 1 ]; then exit 0; fi\n'
        "    exit 1\n"
        "  fi\n"
        '  if [ "$arg" = "verify" ]; then\n'
        f'    n=$(cat "{verify_count}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{verify_count}"\n'
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
        '  *"We are now in the Refactor phase"*) echo refactor >> "' + str(refactors) + '" ;;\n'
        '  *"We are now in the Green phase"*)\n'
        "    printf 'def product():\\n    return 1\\n' > product.py\n"
        "    git add product.py\n"
        '    git commit -m "Green" >/dev/null ;;\n'
        '  *"mutation hunting phase"*) echo kill >> "' + str(hunts) + '" ;;\n'
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

    with pytest.raises(SystemExit):
        tdd()

    written = (target / "harness.log").read_text().splitlines()
    assert (
        "--- TDD Mutants survived 1 of 10 ---" in written,
        hunts.exists(),
        refactors.exists(),
    ) == (True, False, False)


def test_tdd_excludes_the_failing_acceptance_test_from_mutants(
    tmp_path, monkeypatch
):
    from harness.tdd import tdd

    target = tmp_path / "target"
    (target / "specs").mkdir(parents=True)
    (target / "specs" / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\nskip = "reason"\n\n'
        '[criteria.verify]\nrun = "pytest tests/test_acceptance_alpha.py::test_a"\n'
    )
    (target / "AGENTS.md").write_text("## Public interface\n\nharness tdd\n")
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\ncalls\n"
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    verify_count = tmp_path / "verify-count"
    calls = tmp_path / "calls"
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "inspect" ]; then exit 0; fi\n'
        'case "$*" in\n'
        '  *"--dry-run mutants"*) exit 0 ;;\n'
        '  *"pytest"*"test_acceptance"*) exit 1 ;;\n'
        "esac\n"
        'for arg in "$@"; do\n'
        '  if [ "$arg" = "qed" ]; then\n'
        "    printf '%s' '{\"specs\": ["
        "{\"spec\": \"alpha\", \"criteria\": [{\"description\": \"A\", \"result\": \"failed\"}]}"
        "]}'\n"
        "    exit 1\n"
        "  fi\n"
        '  if [ "$arg" = "mutants" ]; then\n'
        f'    echo "$*" >> "{calls}"\n'
        "    exit 0\n"
        "  fi\n"
        '  if [ "$arg" = "verify" ]; then\n'
        f'    n=$(cat "{verify_count}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{verify_count}"\n'
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

    assert "ACTIVE=tests/test_acceptance_alpha.py::test_a" in calls.read_text()


def test_tdd_resets_a_rejected_cycle_to_its_base(tmp_path, monkeypatch):
    from harness.tdd import tdd

    target = tmp_path / "target"
    (target / "specs").mkdir(parents=True)
    (target / "specs" / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\nskip = "reason"\n\n'
        '[criteria.verify]\nrun = "true"\n'
    )
    (target / "AGENTS.md").write_text("## Public interface\n\nharness tdd\n")
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    verify_count = tmp_path / "verify-count"
    mutant_count = tmp_path / "mutant-count"
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "inspect" ]; then\n'
        "  exit 0\n"
        "fi\n"
        'case "$*" in\n'
        '  *"--dry-run mutants"*) exit 0 ;;\n'
        "esac\n"
        'for arg in "$@"; do\n'
        '  if [ "$arg" = "qed" ]; then\n'
        "    printf '%s' '{\"specs\": ["
        "{\"spec\": \"alpha\", \"criteria\": [{\"description\": \"A\", \"result\": \"failed\"}]}"
        "]}'\n"
        "    exit 1\n"
        "  fi\n"
        '  if [ "$arg" = "mutants" ]; then\n'
        f'    n=$(cat "{mutant_count}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{mutant_count}"\n'
        '    if [ "$n" -eq 1 ]; then exit 0; fi\n'
        "    exit 1\n"
        "  fi\n"
        '  if [ "$arg" = "verify" ]; then\n'
        f'    n=$(cat "{verify_count}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{verify_count}"\n'
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
        'case "$*" in\n'
        '  *"acceptance-test Red phase"*)\n'
        "    mkdir -p tests\n"
        "    printf 'def test_acceptance():\\n    pass\\n' > tests/test_acceptance.py\n"
        "    git add tests/test_acceptance.py\n"
        '    git commit -m "Acceptance" >/dev/null ;;\n'
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

    with pytest.raises(SystemExit):
        tdd()

    subjects = subprocess.run(
        ["git", "log", "--format=%s"], cwd=target, capture_output=True, text=True
    ).stdout.splitlines()
    assert (
        any("Activate the A acceptance criterion" in subject for subject in subjects),
        "Acceptance" in subjects,
        "Fail" in subjects,
        "Green" in subjects,
    ) == (True, True, False, False)


def test_tdd_cleans_untracked_files_and_keeps_the_log(tmp_path, monkeypatch):
    from harness.tdd import tdd

    target = tmp_path / "target"
    (target / "specs").mkdir(parents=True)
    (target / "specs" / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\nskip = "reason"\n\n'
        '[criteria.verify]\nrun = "true"\n'
    )
    (target / "AGENTS.md").write_text("## Public interface\n\nharness tdd\n")
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    verify_count = tmp_path / "verify-count"
    mutant_count = tmp_path / "mutant-count"
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "inspect" ]; then\n'
        "  exit 0\n"
        "fi\n"
        'case "$*" in\n'
        '  *"--dry-run mutants"*) exit 0 ;;\n'
        "esac\n"
        'for arg in "$@"; do\n'
        '  if [ "$arg" = "qed" ]; then\n'
        "    printf '%s' '{\"specs\": ["
        "{\"spec\": \"alpha\", \"criteria\": [{\"description\": \"A\", \"result\": \"failed\"}]}"
        "]}'\n"
        "    exit 1\n"
        "  fi\n"
        '  if [ "$arg" = "mutants" ]; then\n'
        f'    n=$(cat "{mutant_count}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{mutant_count}"\n'
        '    if [ "$n" -eq 1 ]; then exit 0; fi\n'
        "    exit 1\n"
        "  fi\n"
        '  if [ "$arg" = "verify" ]; then\n'
        f'    n=$(cat "{verify_count}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{verify_count}"\n'
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
        'case "$*" in\n'
        '  *"acceptance-test Red phase"*)\n'
        "    mkdir -p tests\n"
        "    printf 'def test_acceptance():\\n    pass\\n' > tests/test_acceptance.py\n"
        "    git add tests/test_acceptance.py\n"
        '    git commit -m "Acceptance" >/dev/null ;;\n'
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
        '  *"We are now in the Green phase"*)\n'
        "    printf 'def product():\\n    return 1\\n' > product.py\n"
        "    printf 'scratch\\n' > leftover.txt\n"
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

    with pytest.raises(SystemExit):
        tdd()

    log = target / "harness.log"
    assert (
        (target / "leftover.txt").exists(),
        log.exists() and "--- TDD Mutants survived 1 of 10 ---" in log.read_text(),
    ) == (False, True)


def test_tdd_aborts_when_mutants_fail_after_the_reset(tmp_path, monkeypatch):
    from harness.tdd import tdd

    target = tmp_path / "target"
    (target / "specs").mkdir(parents=True)
    (target / "specs" / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\nskip = "reason"\n\n'
        '[criteria.verify]\nrun = "true"\n'
    )
    (target / "AGENTS.md").write_text("## Public interface\n\nharness tdd\n")
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    verify_count = tmp_path / "verify-count"
    mutant_count = tmp_path / "mutant-count"
    mutants = tmp_path / "mutants"
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "inspect" ]; then\n'
        "  exit 0\n"
        "fi\n"
        'case "$*" in\n'
        '  *"--dry-run mutants"*) exit 0 ;;\n'
        "esac\n"
        'for arg in "$@"; do\n'
        '  if [ "$arg" = "qed" ]; then\n'
        "    printf '%s' '{\"specs\": ["
        "{\"spec\": \"alpha\", \"criteria\": [{\"description\": \"A\", \"result\": \"failed\"}]}"
        "]}'\n"
        "    exit 1\n"
        "  fi\n"
        '  if [ "$arg" = "mutants" ]; then\n'
        f'    n=$(cat "{mutant_count}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{mutant_count}"\n'
        '    if [ "$n" -eq 1 ]; then exit 0; fi\n'
        f'    echo mutants >> "{mutants}"\n'
        "    exit 1\n"
        "  fi\n"
        '  if [ "$arg" = "verify" ]; then\n'
        f'    n=$(cat "{verify_count}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{verify_count}"\n'
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

    with pytest.raises(SystemExit) as exit_info:
        tdd()

    assert (len(mutants.read_text().splitlines()), exit_info.value.code) == (2, 1)


def test_tdd_restarts_the_cycle_after_a_passing_recheck(tmp_path, monkeypatch):
    from harness.tdd import tdd

    target = tmp_path / "target"
    (target / "specs").mkdir(parents=True)
    (target / "specs" / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\nskip = "reason"\n\n'
        '[criteria.verify]\nrun = "true"\n'
    )
    (target / "AGENTS.md").write_text("## Public interface\n\nharness tdd\n")
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    verify_count = tmp_path / "verify-count"
    mutant_count = tmp_path / "mutant-count"
    reds = tmp_path / "reds"
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "inspect" ]; then\n'
        "  exit 0\n"
        "fi\n"
        'case "$*" in\n'
        '  *"--dry-run mutants"*) exit 0 ;;\n'
        "esac\n"
        'for arg in "$@"; do\n'
        '  if [ "$arg" = "qed" ]; then\n'
        "    printf '%s' '{\"specs\": ["
        "{\"spec\": \"alpha\", \"criteria\": [{\"description\": \"A\", \"result\": \"failed\"}]}"
        "]}'\n"
        "    exit 1\n"
        "  fi\n"
        '  if [ "$arg" = "mutants" ]; then\n'
        f'    n=$(cat "{mutant_count}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{mutant_count}"\n'
        '    if [ "$n" -eq 2 ]; then exit 1; fi\n'
        "    exit 0\n"
        "  fi\n"
        '  if [ "$arg" = "verify" ]; then\n'
        f'    n=$(cat "{verify_count}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{verify_count}"\n'
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
        "    echo red >> \"" + str(reds) + "\"\n"
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

    try:
        tdd()
    except SystemExit:
        pass

    assert (
        len(reds.read_text().splitlines()),
        verify_count.read_text().strip(),
    ) == (2, "3")


def test_tdd_counts_the_rejected_cycles(tmp_path, monkeypatch):
    from harness.tdd import tdd

    target = tmp_path / "target"
    (target / "specs").mkdir(parents=True)
    (target / "specs" / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\nskip = "reason"\n\n'
        '[criteria.verify]\nrun = "true"\n'
    )
    (target / "AGENTS.md").write_text("## Public interface\n\nharness tdd\n")
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    verify_count = tmp_path / "verify-count"
    mutant_count = tmp_path / "mutant-count"
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "inspect" ]; then\n'
        "  exit 0\n"
        "fi\n"
        'case "$*" in\n'
        '  *"--dry-run mutants"*) exit 0 ;;\n'
        "esac\n"
        'for arg in "$@"; do\n'
        '  if [ "$arg" = "qed" ]; then\n'
        "    printf '%s' '{\"specs\": ["
        "{\"spec\": \"alpha\", \"criteria\": [{\"description\": \"A\", \"result\": \"failed\"}]}"
        "]}'\n"
        "    exit 1\n"
        "  fi\n"
        '  if [ "$arg" = "mutants" ]; then\n'
        f'    n=$(cat "{mutant_count}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{mutant_count}"\n'
        '    case "$n" in 2|4) exit 1 ;; esac\n'
        "    exit 0\n"
        "  fi\n"
        '  if [ "$arg" = "verify" ]; then\n'
        f'    n=$(cat "{verify_count}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{verify_count}"\n'
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
    assert (
        written.count("--- TDD Mutants survived 1 of 10 ---"),
        written.count("--- TDD Mutants survived 2 of 10 ---"),
    ) == (1, 1)


def test_tdd_stops_at_the_streak_limit(tmp_path, monkeypatch):
    from harness.tdd import tdd

    target = tmp_path / "target"
    (target / "specs").mkdir(parents=True)
    (target / "specs" / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\nskip = "reason"\n\n'
        '[criteria.verify]\nrun = "true"\n'
    )
    (target / "AGENTS.md").write_text("## Public interface\n\nharness tdd\n")
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    verify_count = tmp_path / "verify-count"
    mutant_count = tmp_path / "mutant-count"
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "inspect" ]; then\n'
        "  exit 0\n"
        "fi\n"
        'case "$*" in\n'
        '  *"--dry-run mutants"*) exit 0 ;;\n'
        "esac\n"
        'for arg in "$@"; do\n'
        '  if [ "$arg" = "qed" ]; then\n'
        "    printf '%s' '{\"specs\": ["
        "{\"spec\": \"alpha\", \"criteria\": [{\"description\": \"A\", \"result\": \"failed\"}]}"
        "]}'\n"
        "    exit 1\n"
        "  fi\n"
        '  if [ "$arg" = "mutants" ]; then\n'
        f'    n=$(cat "{mutant_count}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{mutant_count}"\n'
        '    case "$n" in 2|4|6) exit 1 ;; esac\n'
        "    exit 0\n"
        "  fi\n"
        '  if [ "$arg" = "verify" ]; then\n'
        f'    n=$(cat "{verify_count}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{verify_count}"\n'
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

    try:
        tdd(max_passes=3)
    except SystemExit as error:
        code = error.code
    else:
        code = None

    assert code == 1


def test_tdd_skips_the_red_when_the_activated_criterion_passes(
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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    record = tmp_path / "record"
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
    pi.write_text(
        "#!/bin/sh\n"
        'case "$*" in\n'
        '  *"acceptance-test Red phase"*) echo atdd-red >> "' + str(record) + '" ;;\n'
        '  *"acceptance phase of the ATDD outer loop"*)\n'
        "    if grep -q '^skip = ' specs/alpha.spec.toml; then\n"
        "      sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "      printf 'Activated A.'\n"
        "    else\n"
        "      printf '<promise>COMPLETE</promise>'\n"
        "    fi ;;\n"
        "  *) : ;;\n"
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

    written = record.read_text().splitlines() if record.exists() else []
    assert "atdd-red" not in written


def test_tdd_verifies_before_the_first_inner_cycle(tmp_path, monkeypatch):
    from harness.tdd import tdd

    target = tmp_path / "target"
    (target / "specs").mkdir(parents=True)
    (target / "specs" / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\nskip = "reason"\n\n'
        '[criteria.verify]\nrun = "true"\n'
    )
    (target / "AGENTS.md").write_text("## Public interface\n\nharness tdd\n")
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    record = tmp_path / "record"
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
        'case "$*" in\n'
        '  *"acceptance-test Red phase"*) : ;;\n'
        '  *"acceptance phase of the ATDD outer loop"*)\n'
        "    if grep -q '^skip = ' specs/alpha.spec.toml; then\n"
        "      sed -i '/^skip = /d' specs/alpha.spec.toml\n"
        "      printf 'Activated A.'\n"
        "    else\n"
        "      printf '<promise>COMPLETE</promise>'\n"
        "    fi ;;\n"
        '  *"Red phase of Test-Driven Development"*) echo afk-red >> "' + str(record) + '" ;;\n'
        "  *) : ;;\n"
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

    written = record.read_text().splitlines() if record.exists() else []
    assert "afk-red" not in written


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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
        "{\"spec\": \"alpha\", \"criteria\": [{\"description\": \"A\", \"result\": \"failed\"}]}"
        "]}'\n"
        "    exit 0\n"
        "  fi\n"
        '  if [ "$arg" = "verify" ]; then\n'
        f'    n=$(cat "{checks}" 2>/dev/null || echo 0)\n'
        "    n=$((n + 1))\n"
        f'    echo "$n" > "{checks}"\n'
        '    if [ "$n" -eq 1 ]; then exit 0; fi\n'
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

    assert events.read_text().splitlines()[-1] == "after pass"


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
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
    assert "(ATDD 1/10)" in cycles[-1]


def test_tdd_counts_the_inner_cycles_of_a_pass(tmp_path, monkeypatch):
    from harness.tdd import tdd

    target = tmp_path / "target"
    (target / "specs").mkdir(parents=True)
    (target / "specs" / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\nskip = "reason"\n\n'
        '[criteria.verify]\nrun = "true"\n'
    )
    (target / "AGENTS.md").write_text("## Public interface\n\nharness tdd\n")
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
        '    if [ "$n" -eq 2 ] || [ "$n" -eq 3 ] || [ "$n" -eq 4 ]; then exit 1; fi\n'
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
    cycles = [line for line in written if line.startswith("--- TDD cycle")]
    assert cycles == [
        "--- TDD cycle 1 (ATDD 1/10) ---",
        "--- TDD cycle 2 (ATDD 1/10) ---",
        "--- TDD cycle 3 (ATDD 1/10) ---",
    ]


def test_tdd_prints_each_phase_header_to_stdout(tmp_path, monkeypatch, capsys):
    from harness.tdd import tdd

    target = tmp_path / "target"
    (target / "specs").mkdir(parents=True)
    (target / "specs" / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\nskip = "reason"\n\n'
        '[criteria.verify]\nrun = "true"\n'
    )
    (target / "AGENTS.md").write_text("## Public interface\n\nharness tdd\n")
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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

    written = (target / "harness.log").read_text().splitlines()
    headers = [
        line
        for line in written
        if line.startswith(("===", "--- TDD", "--- Refactor"))
    ]
    assert capsys.readouterr().out.splitlines() == headers


def test_waiting_animation_is_silent_without_a_terminal(monkeypatch):
    from harness.tdd import _waiting

    class Terminal:
        def __init__(self):
            self.text = ""

        def isatty(self):
            return False

        def write(self, text):
            self.text += text

        def flush(self):
            pass

    terminal = Terminal()
    monkeypatch.setattr(sys, "stdout", terminal)

    with _waiting():
        pass

    assert terminal.text == ""


def test_waiting_animation_writes_a_frame_on_a_terminal(monkeypatch):
    from harness.tdd import _waiting

    class Terminal:
        def __init__(self):
            self.text = ""

        def isatty(self):
            return True

        def write(self, text):
            self.text += text

        def flush(self):
            pass

    terminal = Terminal()
    monkeypatch.setattr(sys, "stdout", terminal)

    with _waiting():
        assert terminal.text != ""


def test_waiting_animation_erases_its_line_when_the_wait_raises(monkeypatch):
    from harness.tdd import _waiting

    class Terminal:
        def __init__(self):
            self.text = ""

        def isatty(self):
            return True

        def write(self, text):
            self.text += text

        def flush(self):
            pass

    terminal = Terminal()
    monkeypatch.setattr(sys, "stdout", terminal)

    with pytest.raises(RuntimeError):
        with _waiting():
            raise RuntimeError

    assert terminal.text.endswith("\r")


def test_tdd_waits_with_a_frame_while_a_prompt_runs(tmp_path, monkeypatch):
    from harness.tdd import tdd

    class Terminal:
        def __init__(self):
            self.text = ""

        def isatty(self):
            return True

        def write(self, text):
            self.text += text

        def flush(self):
            pass

    target = tmp_path / "target"
    (target / "specs").mkdir(parents=True)
    (target / "specs" / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\nskip = "reason"\n\n'
        '[criteria.verify]\nrun = "true"\n'
    )
    (target / "AGENTS.md").write_text("## Public interface\n\nharness tdd\n")
    (target / ".gitignore").write_text(
        "harness.log\nscore-before.txt\nscore-after.txt\n"
    )
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
    terminal = Terminal()
    monkeypatch.setattr(sys, "stdout", terminal)

    tdd()

    assert "\r|" in terminal.text


def test_waiting_animation_cycles_frames_on_a_terminal(monkeypatch):
    from harness.tdd import _waiting

    class Terminal:
        def __init__(self):
            self.text = ""

        def isatty(self):
            return True

        def write(self, text):
            self.text += text

        def flush(self):
            pass

    terminal = Terminal()
    monkeypatch.setattr(sys, "stdout", terminal)

    with _waiting():
        time.sleep(0.5)

    frames = {char for char in terminal.text if char in "|/-\\"}
    assert len(frames) > 1


def test_waiting_animation_stops_when_the_wait_ends(monkeypatch):
    from harness.tdd import _waiting

    class Terminal:
        def __init__(self):
            self.text = ""

        def isatty(self):
            return True

        def write(self, text):
            self.text += text

        def flush(self):
            pass

    terminal = Terminal()
    monkeypatch.setattr(sys, "stdout", terminal)

    with _waiting():
        time.sleep(0.5)

    written = terminal.text
    time.sleep(0.5)

    assert terminal.text == written
