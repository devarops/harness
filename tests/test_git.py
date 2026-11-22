"""Tests for the harness git module."""

import pytest


def test_status_aborts_outside_a_repository(tmp_path):
    from harness.git import status

    with pytest.raises(SystemExit) as exit_info:
        status(tmp_path)

    assert exit_info.value.code == 1
