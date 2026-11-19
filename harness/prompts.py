"""Run the harness prompts through pi."""

import subprocess
from pathlib import Path


def run_prompt(prompt_path: Path) -> None:
    """Run the prompt in the given file through pi.

    Args:
        prompt_path: The path to the prompt file.

    Raises:
        SystemExit: If pi exits non-zero.
    """
    prompt = prompt_path.read_text()
    pi_command = ["pi", "--no-session", "--print", prompt]
    result = subprocess.run(pi_command)
    if result.returncode != 0:
        raise SystemExit(1)
