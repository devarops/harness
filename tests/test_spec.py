"""Tests for the harness spec module."""


def test_import_specs_without_specs_returns_empty(tmp_path):
    from harness.spec import import_specs

    assert import_specs(tmp_path) == []


def test_import_specs_returns_the_single_spec(tmp_path):
    from harness.spec import import_specs

    path = tmp_path / "specs" / "alpha.spec.toml"
    path.parent.mkdir()
    path.write_text('name = "alpha"\n')

    assert [(spec.path, spec.name) for spec in import_specs(tmp_path)] == [(path, "alpha")]
