"""Run the harness prompts through pi."""

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

_PI_COMMAND = ("pi", "--no-session", "--print")
_FAILURE_EXIT_CODE = 1
_COMPLETE_MARKER = "<promise>COMPLETE</promise>"
_FAILURE_PATTERN = r"<error>FAIL: (.*?)</error>"


@dataclass(frozen=True)
class PromptResult:
    """The outcome of running a prompt."""

    complete: bool
    failure: Optional[str]
    output: str


def _run_pi(prompt: str, model: Optional[str]) -> subprocess.CompletedProcess:
    """Run pi with the prompt text and the selected model.

    Args:
        prompt: The prompt text.
        model: The model to name for pi, or None for pi's own.

    Returns:
        The completed process.
    """
    pi_command = [*_PI_COMMAND]
    if model:
        pi_command.extend(["--models", model])
    pi_command.append(prompt)
    return subprocess.run(pi_command, capture_output=True, text=True)


def _parse_result(output: str) -> PromptResult:
    """Return the result described by a captured prompt output."""
    complete = _COMPLETE_MARKER in output
    failure_match = re.search(_FAILURE_PATTERN, output)
    failure = failure_match.group(1) if failure_match else None
    return PromptResult(complete=complete, failure=failure, output=output)


def run_prompt(prompt_path: Path, model: Optional[str] = None) -> PromptResult:
    """Run the prompt in the given file through pi.

    Args:
        prompt_path: The path to the prompt file.
        model: The model to name for pi, or None for pi's own.

    Returns:
        The prompt result.

    Raises:
        SystemExit: If pi exits non-zero.
    """
    prompt = prompt_path.read_text()
    completed = _run_pi(prompt, model)
    if completed.returncode != 0:
        raise SystemExit(_FAILURE_EXIT_CODE)
    return _parse_result(completed.stdout)
