"""Tests for the harness git module."""

import subprocess

import pytest


def test_status_aborts_outside_a_repository(tmp_path):
    from harness.git import status

    with pytest.raises(SystemExit) as exit_info:
        status(tmp_path)

    assert exit_info.value.code == 1


def test_commit_with_nothing_staged_aborts(tmp_path, monkeypatch):
    from harness.git import commit

    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    monkeypatch.setenv("GIT_AUTHOR_NAME", "Harness")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "harness@example.com")
    monkeypatch.setenv("GIT_COMMITTER_NAME", "Harness")
    monkeypatch.setenv("GIT_COMMITTER_EMAIL", "harness@example.com")

    with pytest.raises(SystemExit) as exit_info:
        commit(tmp_path, "Record the change.")

    assert exit_info.value.code == 1


def test_head_without_commits_aborts(tmp_path):
    from harness.git import head

    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)

    with pytest.raises(SystemExit) as exit_info:
        head(tmp_path)

    assert exit_info.value.code == 1


def test_clean_tree_has_no_changed_paths(tmp_path):
    from harness.git import changed_paths

    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)

    assert changed_paths(tmp_path) == []


def test_changed_paths_lists_a_staged_path(tmp_path):
    from harness.git import changed_paths

    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    (tmp_path / "alpha.txt").write_text("A\n")
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", "alpha.txt"],
        check=True,
        capture_output=True,
    )

    assert changed_paths(tmp_path) == ["alpha.txt"]


def test_commit_paths_lists_the_last_commit_path(tmp_path, monkeypatch):
    from harness.git import commit_paths

    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    monkeypatch.setenv("GIT_AUTHOR_NAME", "Harness")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "harness@example.com")
    monkeypatch.setenv("GIT_COMMITTER_NAME", "Harness")
    monkeypatch.setenv("GIT_COMMITTER_EMAIL", "harness@example.com")
    (tmp_path / "alpha.txt").write_text("A\n")
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", "alpha.txt"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-m", "Record alpha."],
        check=True,
        capture_output=True,
    )

    assert commit_paths(tmp_path) == ["alpha.txt"]


def test_commit_records_the_staged_path(tmp_path, monkeypatch):
    from harness.git import changed_paths, commit, commit_paths

    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    monkeypatch.setenv("GIT_AUTHOR_NAME", "Harness")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "harness@example.com")
    monkeypatch.setenv("GIT_COMMITTER_NAME", "Harness")
    monkeypatch.setenv("GIT_COMMITTER_EMAIL", "harness@example.com")
    (tmp_path / "alpha.txt").write_text("A\n")
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", "alpha.txt"],
        check=True,
        capture_output=True,
    )

    commit(tmp_path, "Record alpha.")

    assert (changed_paths(tmp_path), commit_paths(tmp_path)) == ([], ["alpha.txt"])


def test_head_matches_the_repository_hash(tmp_path, monkeypatch):
    from harness.git import head

    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    monkeypatch.setenv("GIT_AUTHOR_NAME", "Harness")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "harness@example.com")
    monkeypatch.setenv("GIT_COMMITTER_NAME", "Harness")
    monkeypatch.setenv("GIT_COMMITTER_EMAIL", "harness@example.com")
    (tmp_path / "alpha.txt").write_text("A\n")
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", "alpha.txt"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-m", "Record alpha."],
        check=True,
        capture_output=True,
    )
    expected = subprocess.run(
        ["git", "-C", str(tmp_path), "rev-parse", "--short", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    assert head(tmp_path) == expected


def test_clean_tree_has_no_diff(tmp_path):
    from harness.git import diff

    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)

    assert diff(tmp_path) == ""


def test_removed_line_is_carried_with_its_minus(tmp_path, monkeypatch):
    from harness.git import diff

    (tmp_path / "spec.toml").write_text('name = "alpha"\nskip = "reason"\n')
    monkeypatch.setenv("GIT_AUTHOR_NAME", "Harness")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "harness@example.com")
    monkeypatch.setenv("GIT_COMMITTER_NAME", "Harness")
    monkeypatch.setenv("GIT_COMMITTER_EMAIL", "harness@example.com")
    subprocess.run(["git", "init", "--quiet"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "--all"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "--quiet", "-m", "Target"], cwd=tmp_path, check=True
    )
    (tmp_path / "spec.toml").write_text('name = "alpha"\n')

    assert '-skip = "reason"' in diff(tmp_path)
