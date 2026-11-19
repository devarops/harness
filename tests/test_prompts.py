"""Tests for the harness prompts module."""

import pytest


def test_nonzero_pi_exit_aborts(tmp_path, monkeypatch):
    from harness.prompts import run_prompt

    prompt = tmp_path / "prompt.md"
    prompt.write_text("Do the thing.")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    pi = bin_dir / "pi"
    pi.write_text("#!/bin/sh\nexit 7\n")
    pi.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))

    with pytest.raises(SystemExit) as exit_info:
        run_prompt(prompt)

    assert exit_info.value.code == 1


def test_plain_output_reports_neither(tmp_path, monkeypatch):
    from harness.prompts import run_prompt

    prompt = tmp_path / "prompt.md"
    prompt.write_text("Do the thing.")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    pi = bin_dir / "pi"
    pi.write_text("#!/bin/sh\nprintf 'ordinary prose'\n")
    pi.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))

    result = run_prompt(prompt)

    assert (result.complete, result.failure) == (False, None)


def test_prompt_output_is_captured(tmp_path, monkeypatch, capfd):
    from harness.prompts import run_prompt

    prompt = tmp_path / "prompt.md"
    prompt.write_text("Do the thing.")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    pi = bin_dir / "pi"
    pi.write_text("#!/bin/sh\nprintf 'ordinary prose'\n")
    pi.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))

    run_prompt(prompt)

    assert capfd.readouterr().out == ""
