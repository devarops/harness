"""Approval tests for the approval module."""

from pathlib import Path

from approval import printer, reject


def test_printer_writes_value_to_received_file():
    printer("hello", "greeting")
    received = Path("tests/approval/greeting.received.txt")
    assert received.read_text() == "hello"
    received.unlink()


def test_reject_deletes_received_file():
    printer("to-delete", "temp")
    reject("temp")
    assert not Path("tests/approval/temp.received.txt").exists()
