"""Tests for the harness scoring module."""

import os


def test_scoring_keeps_the_valid_counts_and_returns_the_median(tmp_path, monkeypatch):
    from harness.scoring import score

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    counter = tmp_path / "runs"
    args = tmp_path / "args"
    pi = bin_dir / "pi"
    pi.write_text(
        "#!/bin/sh\n"
        f'printf \'%s\\n\' "$@" >> "{args}"\n'
        'case "$*" in\n'
        '  *"Commit: abc123"*) ;;\n'
        "  *) printf 'missing parameters'; exit 1 ;;\n"
        "esac\n"
        f'n=$(cat "{counter}" 2>/dev/null || echo 0)\n'
        "n=$((n + 1))\n"
        f'echo "$n" > "{counter}"\n'
        'case "$n" in\n'
        "  1) printf '<score>5</score>' ;;\n"
        "  2) printf 'not a score' ;;\n"
        "  3) printf '<score>6</score>' ;;\n"
        "esac\n"
    )
    pi.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    prompt = tmp_path / "prompt.md"
    prompt.write_text("Score the files.")
    count_file = tmp_path / "count.txt"

    result = score("abc123", ["src/a.py"], count_file, prompt)

    assert (count_file.read_text().splitlines(), result) == (["5", "6"], 5.5)
