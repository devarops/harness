"""Approval tests for the approval module."""

from pathlib import Path

from approval import printer


def test_printer_writes_value_to_received_file():
    printer("hello", "greeting")
    received = Path("tests/approval/greeting.received.txt")
    assert received.read_text() == "hello"
    received.unlink()
