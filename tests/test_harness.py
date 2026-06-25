"""Approval tests for the harness package metadata."""

from harness import version


def test_version():
    expected_version = "0.1.0"
    obtained_version = version()
    assert obtained_version == expected_version
