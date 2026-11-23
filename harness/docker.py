"""Run commands in the development container."""

import subprocess
from pathlib import Path

_INSPECT_COMMAND = ("docker", "inspect")
_EXEC_COMMAND = ("docker", "exec", "--workdir")
_FAILURE_EXIT_CODE = 1
WORKDIR = Path("/workdir")


def run(container: str, command: list[str], workdir: Path) -> subprocess.CompletedProcess:
    """Run a command in the development container.

    Args:
        container: The container name.
        command: The command and its arguments.
        workdir: The working directory inside the container.

    Returns:
        The completed process.

    Raises:
        SystemExit: If the container is missing.
    """
    inspected = subprocess.run([*_INSPECT_COMMAND, container], capture_output=True)
    if inspected.returncode != 0:
        raise SystemExit(_FAILURE_EXIT_CODE)
    return subprocess.run(
        [*_EXEC_COMMAND, str(workdir), container, *command],
        capture_output=True,
        text=True,
    )
