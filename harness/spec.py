"""Read the acceptance specifications."""

from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 and earlier
    import tomli as tomllib


@dataclass(frozen=True)
class Spec:
    """A specification file and its declared name."""

    path: Path
    name: str


def import_specs(root):
    """Return the specs under the repository root."""
    return [_import_spec(path) for path in sorted((root / "specs").glob("*.spec.toml"))]


def _import_spec(path):
    """Return the spec declared in a TOML file."""
    return Spec(path, tomllib.loads(path.read_text())["name"])
