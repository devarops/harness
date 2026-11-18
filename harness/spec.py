"""Read the acceptance specifications."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 and earlier
    import tomli as tomllib


@dataclass(frozen=True)
class Criterion:
    """A criterion declared in a specification."""

    description: str
    verify: str
    skip: Optional[str] = None


@dataclass(frozen=True)
class Spec:
    """A specification file and its declared name."""

    path: Path
    name: str
    criteria: list = field(default_factory=list)


def import_specs(root):
    """Return the specs under the repository root."""
    specs = []
    seen_names = set()
    for path in _spec_paths(root):
        spec = _import_spec(path)
        _record_unique_name(spec.name, seen_names)
        specs.append(spec)
    return specs


def is_spec_present(root):
    """Return whether the repository has a top-level spec."""
    return any(_spec_paths(root))


def _record_unique_name(name, seen_names):
    """Record a spec name, rejecting a repeat."""
    if name in seen_names:
        raise ValueError(f"duplicate spec name: {name}")
    seen_names.add(name)


def _spec_paths(root):
    """Return the top-level spec paths under the repository root in order."""
    return sorted((root / "specs").glob("*.spec.toml"))


def _import_spec(path):
    """Return the spec declared in a TOML file."""
    data = tomllib.loads(path.read_text())
    criteria = data.get("criteria", [])
    _check_required_fields(criteria, path)
    parsed_criteria = [_parse_criterion(item) for item in criteria]
    return Spec(path, data["name"], parsed_criteria)


def _parse_criterion(item):
    """Return the criterion declared in a TOML table."""
    command = item["verify"]["run"]
    return Criterion(item["description"], command, item.get("skip"))


def _check_required_fields(criteria, path):
    """Reject a criterion that lacks a required field."""
    for criterion in criteria:
        if "description" not in criterion:
            raise ValueError(f"criterion without a description in {path}")
        if "verify" not in criterion:
            raise ValueError(f"criterion without a verify block in {path}")
        _check_run_command(criterion["verify"], path)


def _check_run_command(verify, path):
    """Reject a verify block that declares no run command."""
    if "run" not in verify:
        raise ValueError(f"criterion without a run command in {path}")
