"""Build the activation commit message."""

from harness.spec import first_sentence

_SUBJECT = "🔧 Activate the {} acceptance criterion"


def activation_message(criterion, report: str) -> str:
    """Return the activation commit message.

    Args:
        criterion: The criterion the acceptance prompt activated.
        report: The activation report.

    Returns:
        The subject, a blank line, and the report.
    """
    subject = _SUBJECT.format(first_sentence(criterion.description))
    return f"{subject}\n\n{report}"
