"""Run qed and read its verification report."""

from pathlib import Path

from harness import docker

_QED_COMMAND = ("qed", "verify", "specs", "--json")
_FAILURE_EXIT_CODE = 1
_CONFIGURATION_EXIT_CODE = 2


def verify(container: str, root: Path, specs: list) -> None:
    """Run qed in the container and read its report.

    Args:
        container: The development container name.
        root: The repository root.
        specs: The TOML specs to map onto the report.

    Raises:
        SystemExit: If qed reports a configuration or usage error.
    """
    completed = docker.run(container, list(_QED_COMMAND), root)
    if completed.returncode == _CONFIGURATION_EXIT_CODE:
        raise SystemExit(_FAILURE_EXIT_CODE)
