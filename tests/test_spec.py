"""Tests for the harness spec module."""


def test_load_specs_without_specs_returns_empty(tmp_path):
    from harness.spec import load_specs

    assert load_specs(tmp_path) == []
