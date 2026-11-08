"""Tests for the harness spec module."""


def test_import_specs_without_specs_returns_empty(tmp_path):
    from harness.spec import import_specs

    assert import_specs(tmp_path) == []
