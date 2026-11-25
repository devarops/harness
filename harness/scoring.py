"""Score a commit against the quality practices."""

import re
from pathlib import Path
from typing import Optional

from harness import prompts

_SCORE_PATTERN = r"<score>(\d+)</score>"
_RUNS = 3


def score(
    commit: str, files: list, count_file: Path, prompt: Path, model=None
) -> Optional[float]:
    """Run the score prompt three times and return the median of the valid counts.

    Args:
        commit: The commit to score.
        files: The paths to score at that commit.
        count_file: The file that receives the valid counts, one per line.
        prompt: The score prompt file.
        model: The model to name for pi, or None for pi's own.

    Returns:
        The median of the valid counts, or None when none is valid.
    """
    text = (
        prompt.read_text()
        + f"\n\nCommit: {commit}\nFiles:\n"
        + "\n".join(files)
    )
    counts = _valid_counts(text, model)
    if not counts:
        return None
    with count_file.open("a") as handle:
        for count in counts:
            handle.write(f"{count}\n")
    return _median(counts)


def _valid_counts(text: str, model) -> list:
    """Run the score prompt and return the valid counts it prints."""
    counts = []
    for _ in range(_RUNS):
        result = prompts.run_text(text, model)
        match = re.search(_SCORE_PATTERN, result.output)
        if match:
            counts.append(int(match.group(1)))
    return counts


def _median(counts: list) -> float:
    """Return the standard median of the counts."""
    ordered = sorted(counts)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[middle])
    return (ordered[middle - 1] + ordered[middle]) / 2
