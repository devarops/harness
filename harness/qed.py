"""Run qed and read its verification report."""

import json
from dataclasses import dataclass
from pathlib import Path

from harness import docker

_QED_COMMAND = ("qed", "verify", "specs", "--json")
_RESULTS = ("passed", "skipped", "failed")
_FAILURE_EXIT_CODE = 1
_CONFIGURATION_EXIT_CODE = 2


@dataclass(frozen=True)
class Report:
    """The verification report qed printed."""

    specs: dict


def _parse_payload(output: str):
    """Return the report declared by a captured qed payload.

    Raises:
        ValueError: If the output is not JSON.
    """
    try:
        payload = json.loads(output)
    except json.JSONDecodeError as error:
        raise ValueError(f"unreadable qed payload: {output}") from error
    if not isinstance(payload.get("specs"), list):
        raise ValueError(f"payload without specs: {output}")
    return payload


def _check_criterion(reported, criterion, spec_name: str) -> None:
    """Reject a reported criterion that does not match its TOML criterion."""
    if not isinstance(reported, dict):
        raise ValueError(f"criterion entry without fields in {spec_name}")
    if reported.get("description") != criterion.description:
        raise ValueError(f"criterion description mismatch in {spec_name}")
    result = reported.get("result")
    if result is None:
        raise ValueError(f"criterion without a result in {spec_name}")
    if result not in _RESULTS:
        raise ValueError(f"unknown criterion result in {spec_name}: {result}")


def _check_criteria(criteria: list, spec) -> None:
    """Reject reported criteria that do not match the TOML spec."""
    if len(criteria) != len(spec.criteria):
        raise ValueError(f"criterion count mismatch for {spec.name}")
    for reported, criterion in zip(criteria, spec.criteria):
        _check_criterion(reported, criterion, spec.name)


def _entry_spec(entry: dict, specs_by_name: dict):
    """Return the spec an entry reports, rejecting a malformed entry."""
    name = entry.get("spec")
    if name is None:
        raise ValueError(f"entry without a spec name: {entry}")
    if name not in specs_by_name:
        raise ValueError(f"unknown spec name: {name}")
    criteria = entry.get("criteria")
    if not isinstance(criteria, list):
        raise ValueError(f"entry without a criteria list: {entry}")
    spec = specs_by_name[name]
    _check_criteria(criteria, spec)
    return spec


def _map_specs(entries: list, specs: list) -> dict:
    """Return each reported spec name mapped to its TOML spec."""
    specs_by_name = {spec.name: spec for spec in specs}
    mapped = {}
    for entry in entries:
        spec = _entry_spec(entry, specs_by_name)
        mapped[spec.name] = spec
    return mapped


def verify(container: str, root: Path, specs: list) -> Report:
    """Run qed in the container and read its report.

    Args:
        container: The development container name.
        root: The repository root.
        specs: The TOML specs to map onto the report.

    Returns:
        The report qed printed, with its specs mapped by name.

    Raises:
        SystemExit: If qed reports a configuration or usage error.
        ValueError: If the payload cannot be read.
    """
    completed = docker.run(container, list(_QED_COMMAND), root)
    if completed.returncode == _CONFIGURATION_EXIT_CODE:
        raise SystemExit(_FAILURE_EXIT_CODE)
    payload = _parse_payload(completed.stdout)
    return Report(specs=_map_specs(payload["specs"], specs))
