"""Tests for the harness qed module."""

import pytest


def test_configuration_error_aborts(tmp_path, monkeypatch):
    from harness.qed import verify

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n" 'if [ "$1" = "inspect" ]; then\n' "  exit 0\n" "fi\n" "exit 2\n"
    )
    docker.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))

    with pytest.raises(SystemExit) as exit_info:
        verify("repo_dev", tmp_path, [])

    assert exit_info.value.code == 1


def test_unreadable_payload_aborts(tmp_path, monkeypatch):
    from harness.qed import verify

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "inspect" ]; then\n'
        "  exit 0\n"
        "fi\n"
        "printf 'not json'\n"
        "exit 1\n"
    )
    docker.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))

    with pytest.raises(ValueError):
        verify("repo_dev", tmp_path, [])


def test_payload_without_specs_aborts(tmp_path, monkeypatch):
    from harness.qed import verify

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "inspect" ]; then\n'
        "  exit 0\n"
        "fi\n"
        "printf '%s' '{\"passed\": false}'\n"
        "exit 1\n"
    )
    docker.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))

    with pytest.raises(ValueError):
        verify("repo_dev", tmp_path, [])


def test_empty_payload_reports_nothing(tmp_path, monkeypatch):
    from harness.qed import verify

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "inspect" ]; then\n'
        "  exit 0\n"
        "fi\n"
        "printf '%s' '{\"specs\": []}'\n"
        "exit 1\n"
    )
    docker.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))

    assert verify("repo_dev", tmp_path, []).specs == {}


def test_entry_without_spec_name_aborts(tmp_path, monkeypatch):
    from harness.qed import verify

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "inspect" ]; then\n'
        "  exit 0\n"
        "fi\n"
        "printf '%s' '{\"specs\": [{\"criteria\": []}]}'\n"
        "exit 1\n"
    )
    docker.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))

    with pytest.raises(ValueError):
        verify("repo_dev", tmp_path, [])


def test_unknown_spec_name_aborts(tmp_path, monkeypatch):
    from harness.qed import verify
    from harness.spec import import_specs

    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    (specs_dir / "alpha.spec.toml").write_text('name = "alpha"\n')
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "inspect" ]; then\n'
        "  exit 0\n"
        "fi\n"
        "printf '%s' '{\"specs\": [{\"spec\": \"ghost\", \"criteria\": []}]}'\n"
        "exit 1\n"
    )
    docker.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))

    with pytest.raises(ValueError):
        verify("repo_dev", tmp_path, import_specs(tmp_path))


def test_malformed_criteria_aborts(tmp_path, monkeypatch):
    from harness.qed import verify
    from harness.spec import import_specs

    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    (specs_dir / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\n\n[criteria.verify]\nrun = "true"\n'
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "inspect" ]; then\n'
        "  exit 0\n"
        "fi\n"
        "printf '%s' '{\"specs\": [{\"spec\": \"alpha\", \"criteria\": \"junk\"}]}'\n"
        "exit 1\n"
    )
    docker.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))

    with pytest.raises(ValueError):
        verify("repo_dev", tmp_path, import_specs(tmp_path))


def test_criterion_count_mismatch_aborts(tmp_path, monkeypatch):
    from harness.qed import verify
    from harness.spec import import_specs

    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    (specs_dir / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\n\n[criteria.verify]\nrun = "true"\n\n'
        '[[criteria]]\ndescription = "B"\n\n[criteria.verify]\nrun = "true"\n'
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "inspect" ]; then\n'
        "  exit 0\n"
        "fi\n"
        "printf '%s' '{\"specs\": [{\"spec\": \"alpha\", "
        "\"criteria\": [{\"description\": \"A\", \"result\": \"passed\"}]}]}'\n"
        "exit 1\n"
    )
    docker.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))

    with pytest.raises(ValueError):
        verify("repo_dev", tmp_path, import_specs(tmp_path))


def test_criterion_description_mismatch_aborts(tmp_path, monkeypatch):
    from harness.qed import verify
    from harness.spec import import_specs

    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    (specs_dir / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\n\n[criteria.verify]\nrun = "true"\n'
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "inspect" ]; then\n'
        "  exit 0\n"
        "fi\n"
        "printf '%s' '{\"specs\": [{\"spec\": \"alpha\", "
        "\"criteria\": [{\"description\": \"B\", \"result\": \"passed\"}]}]}'\n"
        "exit 1\n"
    )
    docker.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))

    with pytest.raises(ValueError):
        verify("repo_dev", tmp_path, import_specs(tmp_path))


def test_criterion_entry_without_fields_aborts(tmp_path, monkeypatch):
    from harness.qed import verify
    from harness.spec import import_specs

    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    (specs_dir / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\n\n[criteria.verify]\nrun = "true"\n'
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "inspect" ]; then\n'
        "  exit 0\n"
        "fi\n"
        "printf '%s' '{\"specs\": [{\"spec\": \"alpha\", \"criteria\": [\"junk\"]}]}'\n"
        "exit 1\n"
    )
    docker.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))

    with pytest.raises(ValueError):
        verify("repo_dev", tmp_path, import_specs(tmp_path))


def test_criterion_without_result_aborts(tmp_path, monkeypatch):
    from harness.qed import verify
    from harness.spec import import_specs

    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    (specs_dir / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\n\n[criteria.verify]\nrun = "true"\n'
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "inspect" ]; then\n'
        "  exit 0\n"
        "fi\n"
        "printf '%s' '{\"specs\": [{\"spec\": \"alpha\", "
        "\"criteria\": [{\"description\": \"A\"}]}]}'\n"
        "exit 1\n"
    )
    docker.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))

    with pytest.raises(ValueError):
        verify("repo_dev", tmp_path, import_specs(tmp_path))


def test_unknown_criterion_result_aborts(tmp_path, monkeypatch):
    from harness.qed import verify
    from harness.spec import import_specs

    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    (specs_dir / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\n\n[criteria.verify]\nrun = "true"\n'
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "inspect" ]; then\n'
        "  exit 0\n"
        "fi\n"
        "printf '%s' '{\"specs\": [{\"spec\": \"alpha\", "
        "\"criteria\": [{\"description\": \"A\", \"result\": \"unknown\"}]}]}'\n"
        "exit 1\n"
    )
    docker.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))

    with pytest.raises(ValueError):
        verify("repo_dev", tmp_path, import_specs(tmp_path))


def test_report_pairs_each_criterion_result(tmp_path, monkeypatch):
    from harness.qed import verify
    from harness.spec import import_specs

    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    (specs_dir / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\n\n[criteria.verify]\nrun = "true"\n'
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "inspect" ]; then\n'
        "  exit 0\n"
        "fi\n"
        "printf '%s' '{\"specs\": [{\"spec\": \"alpha\", "
        "\"criteria\": [{\"description\": \"A\", \"result\": \"skipped\"}]}]}'\n"
        "exit 1\n"
    )
    docker.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))

    report = verify("repo_dev", tmp_path, import_specs(tmp_path))

    assert report.results == {"alpha": ["skipped"]}


def test_report_names_the_failed_criterion(tmp_path, monkeypatch):
    from harness.qed import verify
    from harness.spec import import_specs

    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    (specs_dir / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\n\n[criteria.verify]\nrun = "true"\n'
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "inspect" ]; then\n'
        "  exit 0\n"
        "fi\n"
        "printf '%s' '{\"specs\": [{\"spec\": \"alpha\", "
        "\"criteria\": [{\"description\": \"A\", \"result\": \"failed\"}]}]}'\n"
        "exit 1\n"
    )
    docker.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))

    report = verify("repo_dev", tmp_path, import_specs(tmp_path))

    assert report.failed == [("alpha", "A")]


def test_report_names_the_skipped_criterion(tmp_path, monkeypatch):
    from harness.qed import verify
    from harness.spec import import_specs

    specs_dir = tmp_path / "specs"
    specs_dir.mkdir()
    (specs_dir / "alpha.spec.toml").write_text(
        'name = "alpha"\n\n'
        '[[criteria]]\ndescription = "A"\n\n[criteria.verify]\nrun = "true"\n'
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "inspect" ]; then\n'
        "  exit 0\n"
        "fi\n"
        "printf '%s' '{\"specs\": [{\"spec\": \"alpha\", "
        "\"criteria\": [{\"description\": \"A\", \"result\": \"skipped\"}]}]}'\n"
        "exit 1\n"
    )
    docker.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))

    report = verify("repo_dev", tmp_path, import_specs(tmp_path))

    assert report.skipped == [("alpha", "A")]
