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
    specs = []
    seen_names = set()
    for path in sorted(_spec_paths(root)):
        spec = _import_spec(path)
        if spec.name in seen_names:
            raise ValueError(f"duplicate spec name: {spec.name}")
        seen_names.add(spec.name)
        specs.append(spec)
    return specs


def is_spec_present(root):
    """Return whether the repository has a top-level spec."""
    return any(_spec_paths(root))


def _spec_paths(root):
    """Return the top-level spec paths under the repository root."""
    return (root / "specs").glob("*.spec.toml")


def _import_spec(path):
    """Return the spec declared in a TOML file."""
    return Spec(path, tomllib.loads(path.read_text())["name"])
