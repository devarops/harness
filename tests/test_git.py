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
