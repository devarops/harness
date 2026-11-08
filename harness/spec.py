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
    paths = sorted((root / "specs").glob("*.spec.toml"))
    return [Spec(path, tomllib.loads(path.read_text())["name"]) for path in paths]
