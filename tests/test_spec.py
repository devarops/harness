"""Tests for the harness spec module."""

import pytest


def _write_spec(root, filename, body):
    """Write a spec file under the root and return its path."""
    path = root / "specs" / filename
    path.parent.mkdir(exist_ok=True)
    path.write_text(body)
    return path


def test_import_specs_without_specs_returns_empty(tmp_path):
    from harness.spec import import_specs

    assert import_specs(tmp_path) == []


def test_import_specs_returns_the_single_spec(tmp_path):
    from harness.spec import import_specs

    path = _write_spec(tmp_path, "alpha.spec.toml", 'name = "alpha"\n')

    assert [(spec.path, spec.name) for spec in import_specs(tmp_path)] == [(path, "alpha")]


def test_spec_without_criteria_has_no_criteria(tmp_path):
    from harness.spec import import_specs

    _write_spec(tmp_path, "alpha.spec.toml", 'name = "alpha"\n')

    assert import_specs(tmp_path)[0].criteria == []


def test_criterion_without_verify_aborts(tmp_path):
    from harness.spec import import_specs

    _write_spec(
        tmp_path,
        "alpha.spec.toml",
        'name = "alpha"\n\n[[criteria]]\ndescription = "A"\n',
    )

    with pytest.raises(ValueError):
        import_specs(tmp_path)


def test_criterion_without_description_aborts(tmp_path):
    from harness.spec import import_specs

    _write_spec(
        tmp_path,
        "alpha.spec.toml",
        'name = "alpha"\n\n[[criteria]]\n\n[criteria.verify]\nrun = "true"\n',
    )

    with pytest.raises(ValueError):
        import_specs(tmp_path)


def test_criterion_verify_without_run_aborts(tmp_path):
    from harness.spec import import_specs

    _write_spec(
        tmp_path,
        "alpha.spec.toml",
        'name = "alpha"\n\n[[criteria]]\ndescription = "A"\n\n'
        '[criteria.verify]\ntype = "command"\n',
    )

    with pytest.raises(ValueError):
        import_specs(tmp_path)


def test_spec_exposes_the_criterion_description(tmp_path):
    from harness.spec import import_specs

    _write_spec(
        tmp_path,
        "alpha.spec.toml",
        'name = "alpha"\n\n[[criteria]]\ndescription = "A"\n\n'
        '[criteria.verify]\nrun = "true"\n',
    )

    criteria = import_specs(tmp_path)[0].criteria
    assert [criterion.description for criterion in criteria] == ["A"]


def test_criterion_without_skip_has_no_reason(tmp_path):
    from harness.spec import import_specs

    _write_spec(
        tmp_path,
        "alpha.spec.toml",
        'name = "alpha"\n\n[[criteria]]\ndescription = "A"\n\n'
        '[criteria.verify]\nrun = "true"\n',
    )

    criterion = import_specs(tmp_path)[0].criteria[0]
    assert criterion.skip is None


def test_criterion_exposes_its_skip_reason(tmp_path):
    from harness.spec import import_specs

    _write_spec(
        tmp_path,
        "alpha.spec.toml",
        'name = "alpha"\n\n[[criteria]]\ndescription = "A"\n'
        'skip = "Not yet"\n\n[criteria.verify]\nrun = "true"\n',
    )

    criterion = import_specs(tmp_path)[0].criteria[0]
    assert criterion.skip == "Not yet"


def test_criterion_exposes_its_verify_command(tmp_path):
    from harness.spec import import_specs

    _write_spec(
        tmp_path,
        "alpha.spec.toml",
        'name = "alpha"\n\n[[criteria]]\ndescription = "A"\n\n'
        '[criteria.verify]\ntype = "command"\nrun = "pytest tests"\n',
    )

    criterion = import_specs(tmp_path)[0].criteria[0]
    assert criterion.verify == "pytest tests"


def test_unknown_spec_name_aborts(tmp_path):
    from harness.spec import import_specs, resolve_specs

    _write_spec(tmp_path, "alpha.spec.toml", 'name = "alpha"\n')

    with pytest.raises(ValueError, match="ghost"):
        resolve_specs(import_specs(tmp_path), ["ghost"])


def test_import_specs_rejects_duplicate_names(tmp_path):
    from harness.spec import import_specs

    _write_spec(tmp_path, "alpha.spec.toml", 'name = "same"\n')
    _write_spec(tmp_path, "beta.spec.toml", 'name = "same"\n')

    with pytest.raises(ValueError, match="same"):
        import_specs(tmp_path)


def test_unsupported_runner_aborts(tmp_path):
    from harness.spec import Criterion, acceptance_test_exists

    criterion = Criterion("A", "cargo test")

    with pytest.raises(ValueError) as error:
        acceptance_test_exists(criterion, tmp_path)

    assert "unsupported" in str(error.value)
