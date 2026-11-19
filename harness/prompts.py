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
    result = subprocess.run(["pi", "--no-session", "--print", prompt])
    if result.returncode != 0:
        raise SystemExit(1)
