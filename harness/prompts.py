"""Run the harness prompts through pi."""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

_PI_COMMAND = ("pi", "--no-session", "--print")


@dataclass(frozen=True)
class PromptResult:
    """The outcome of running a prompt."""

    complete: bool
    failure: Optional[str]


def run_prompt(prompt_path: Path) -> PromptResult:
    """Run the prompt in the given file through pi.

    Args:
        prompt_path: The path to the prompt file.

    Returns:
        The prompt result.

    Raises:
        SystemExit: If pi exits non-zero.
    """
    prompt = prompt_path.read_text()
    pi_command = [*_PI_COMMAND, prompt]
    completed = subprocess.run(pi_command)
    if completed.returncode != 0:
        raise SystemExit(1)
    return PromptResult(complete=False, failure=None)
