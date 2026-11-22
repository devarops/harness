"""Build the activation commit message."""

_SUBJECT = "🔧 Activate the {} acceptance criterion"


def activation_message(criterion, report: str) -> str:
    """Return the activation commit message.

    Args:
        criterion: The criterion the acceptance prompt activated.
        report: The activation report.

    Returns:
        The subject, a blank line, and the report.
    """
    return f"{_SUBJECT.format(criterion.description)}\n\n{report}"
