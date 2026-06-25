"""Approval tests for the approval module."""

from pathlib import Path

from approval import printer, reject, approve


def test_printer_writes_value_to_received_file():
    printer("hello", "greeting")
    received = Path("tests/approval/greeting.received.txt")
    assert received.read_text() == "hello"
    received.unlink()


def test_reject_deletes_received_file():
    printer("to-delete", "temp")
    reject("temp")
    assert not Path("tests/approval/temp.received.txt").exists()


def test_approve_promotes_received_to_approved():
    printer("hello", "demo")
    approve("demo")
    approved = Path("tests/approval/demo.approved.txt")
    received = Path("tests/approval/demo.received.txt")
    assert approved.read_text() == "hello"
    assert not received.exists()
    Path("tests/approval/demo.approved.txt").unlink()
