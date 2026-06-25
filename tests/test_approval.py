"""Approval tests for the approval module."""

from pathlib import Path

from approval import printer, reject, approve, review


def test_printer_writes_value_to_received_file():
    printer("hello", "greeting")
    received = Path("tests/approval/greeting.received.txt")
    assert received.read_text() == "hello"
    received.unlink()


def test_reject_deletes_received_file():
    printer("to-delete", "temp")
    reject("temp")
    assert not Path("tests/approval/temp.received.txt").exists()


def test_approve_copies_received_to_approved_and_preserves_received():
    printer("hello", "demo")
    approve("demo")
    approved = Path("tests/approval/demo.approved.txt")
    received = Path("tests/approval/demo.received.txt")
    assert approved.read_text() == "hello"
    assert received.exists()
    assert received.read_text() == "hello"
    approved.unlink()
    received.unlink()


def test_review_shows_diff_between_approved_and_received():
    approved = Path("tests/approval/demo.approved.txt")
    received = Path("tests/approval/demo.received.txt")
    approved.write_text("line one\n")
    received.write_text("line two\n")
    diff = review("demo")
    assert "-line one" in diff
    assert "+line two" in diff
    assert "approved" in diff
    assert "received" in diff
    approved.unlink()
    received.unlink()
