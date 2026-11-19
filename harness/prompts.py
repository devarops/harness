"""Run the harness prompts through pi."""

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

_PI_COMMAND = ("pi", "--no-session", "--print")
_FAILURE_EXIT_CODE = 1
_COMPLETE_MARKER = "<promise>COMPLETE</promise>"


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
    completed = subprocess.run(pi_command, capture_output=True, text=True)
    if completed.returncode != 0:
        raise SystemExit(_FAILURE_EXIT_CODE)
    complete = _COMPLETE_MARKER in completed.stdout
    failure_match = re.search(r"<error>FAIL: (.*?)</error>", completed.stdout)
    failure = failure_match.group(1) if failure_match else None
    return PromptResult(complete=complete, failure=failure)
