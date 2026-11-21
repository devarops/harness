"""Run commands in the development container."""

import subprocess
from pathlib import Path

_INSPECT_COMMAND = ("docker", "inspect")
_FAILURE_EXIT_CODE = 1


def run(container: str, command: list[str], workdir: Path) -> None:
    """Run a command in the development container.

    Args:
        container: The container name.
        command: The command and its arguments.
        workdir: The working directory inside the container.

    Raises:
        SystemExit: If the container is missing.
    """
    inspected = subprocess.run([*_INSPECT_COMMAND, container], capture_output=True)
    if inspected.returncode != 0:
        raise SystemExit(_FAILURE_EXIT_CODE)
