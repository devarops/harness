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


def test_complete_marker_reports_complete(tmp_path, monkeypatch):
    from harness.prompts import run_prompt

    prompt = tmp_path / "prompt.md"
    prompt.write_text("Do the thing.")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    pi = bin_dir / "pi"
    pi.write_text("#!/bin/sh\nprintf '<promise>COMPLETE</promise>'\n")
    pi.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))

    result = run_prompt(prompt)

    assert result.complete is True


def test_fail_marker_reports_reason(tmp_path, monkeypatch):
    from harness.prompts import run_prompt

    prompt = tmp_path / "prompt.md"
    prompt.write_text("Do the thing.")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    pi = bin_dir / "pi"
    pi.write_text("#!/bin/sh\nprintf '<error>FAIL: reason</error>'\n")
    pi.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))

    result = run_prompt(prompt)

    assert result.failure == "reason"


def test_empty_output_is_carried_as_empty_text(tmp_path, monkeypatch):
    from harness.prompts import run_prompt

    prompt = tmp_path / "prompt.md"
    prompt.write_text("Do the thing.")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    pi = bin_dir / "pi"
    pi.write_text("#!/bin/sh\nexit 0\n")
    pi.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))

    result = run_prompt(prompt)

    assert result.output == ""


def test_two_lines_and_a_marker_are_carried(tmp_path, monkeypatch):
    from harness.prompts import run_prompt

    prompt = tmp_path / "prompt.md"
    prompt.write_text("Do the thing.")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\nprintf 'first line\\n<promise>COMPLETE</promise>\\n'\n"
    )
    pi.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))

    result = run_prompt(prompt)

    assert (result.output, result.complete) == (
        "first line\n<promise>COMPLETE</promise>\n",
        True,
    )


def test_no_model_is_not_passed(tmp_path, monkeypatch):
    from harness.prompts import run_prompt

    prompt = tmp_path / "prompt.md"
    prompt.write_text("Do the thing.")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    recorded = tmp_path / "args.txt"
    pi = bin_dir / "pi"
    pi.write_text(f'#!/bin/sh\nprintf \'%s\\n\' "$@" > "{recorded}"\n')
    pi.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))

    run_prompt(prompt, None)

    assert "--models" not in recorded.read_text()


def test_named_model_is_passed_before_the_prompt(tmp_path, monkeypatch):
    from harness.prompts import run_prompt

    prompt = tmp_path / "prompt.md"
    prompt.write_text("Do the thing.")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    recorded = tmp_path / "args.txt"
    pi = bin_dir / "pi"
    pi.write_text(f'#!/bin/sh\nprintf \'%s\\n\' "$@" > "{recorded}"\n')
    pi.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))

    run_prompt(prompt, "deepseek/v4")

    assert recorded.read_text().splitlines() == [
        "--no-session",
        "--print",
        "--models",
        "deepseek/v4",
        "Do the thing.",
    ]
