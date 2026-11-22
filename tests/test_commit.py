"""Tests for the harness commit module."""


def test_criterion_without_sentence_terminator_becomes_the_subject():
    from harness.commit import activation_message
    from harness.spec import Criterion

    criterion = Criterion("Record the score", "pytest tests/test_score.py::test_record")

    message = activation_message(criterion, "Activated the criterion.")

    assert message == (
        "🔧 Activate the Record the score acceptance criterion\n\n"
        "Activated the criterion."
    )
