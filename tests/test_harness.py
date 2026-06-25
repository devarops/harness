"""Approval tests for the harness package metadata."""

from harness import version


def test_version(approval):
    version()
    approval("version")
