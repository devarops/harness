"""Tests for the harness log module."""


def test_append_creates_the_log_when_absent(tmp_path):
    from harness.log import append

    append(tmp_path, "First line.")

    assert (tmp_path / "harness.log").read_text() == "First line.\n"


def test_append_adds_to_an_existing_log(tmp_path):
    from harness.log import append

    append(tmp_path, "First line.")
    append(tmp_path, "Second line.")

    assert (tmp_path / "harness.log").read_text() == "First line.\nSecond line.\n"
