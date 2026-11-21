"""Read the acceptance specifications."""

import re
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


_PYTEST_PREFIX = "pytest "
_RSCRIPT_PREFIX = "Rscript "
_NODE_SEPARATOR = "::"
_PYTEST_DEF_PREFIX = "def "
_TESTTHAT_FILE_PATTERN = r"test_file\('([^']+)'"
_TESTTHAT_DESCRIBE_PREFIX = 'describe("'
_SENTENCE_PATTERN = r"(.+?[.!?])(?:\s|$)"
_SHELLSPEC_PREFIX = "shellspec "
_SUPPORTED_RUNNERS = (_PYTEST_PREFIX, _RSCRIPT_PREFIX, _SHELLSPEC_PREFIX)


def _malformed_command(runner: str, verify: str) -> ValueError:
    """Return the error for a verify command that omits its target."""
    return ValueError(f"malformed {runner} command: {verify}")


def _pytest_target(verify: str) -> tuple[str, str]:
    """Return the file and node from a pytest verify command.

    Args:
        verify: The verify command.

    Returns:
        The file path and test node.

    Raises:
        ValueError: If the target is malformed.
    """
    target = verify.removeprefix(_PYTEST_PREFIX)
    file_path, separator, node = target.partition(_NODE_SEPARATOR)
    if not separator or not file_path.strip() or not node.strip():
        raise _malformed_command("pytest", verify)
    return file_path, node


def _file_contains(root: Path, file_path: str, text: str) -> bool:
    """Return whether the file under root exists and contains text."""
    path = root / file_path
    return path.is_file() and text in path.read_text()


def _pytest_test_exists(verify: str, root: Path) -> bool:
    """Return whether the pytest verify target exists."""
    file_path, node = _pytest_target(verify)
    return _file_contains(root, file_path, f"{_PYTEST_DEF_PREFIX}{node}(")


def _testthat_file(verify: str) -> str:
    """Return the file from a testthat verify command.

    Args:
        verify: The verify command.

    Returns:
        The test file path.

    Raises:
        ValueError: If the command has no test file.
    """
    match = re.search(_TESTTHAT_FILE_PATTERN, verify)
    if not match:
        raise _malformed_command("testthat", verify)
    return match.group(1)


def _shellspec_file(verify: str) -> str:
    """Return the file from a ShellSpec verify command.

    Args:
        verify: The verify command.

    Returns:
        The test file path.

    Raises:
        ValueError: If the command names no file.
    """
    file_path = verify.removeprefix(_SHELLSPEC_PREFIX).strip()
    if not file_path:
        raise _malformed_command("shellspec", verify)
    return file_path


def _first_sentence(text: str) -> str:
    """Return the first sentence of text on one line."""
    normalized = " ".join(text.split())
    match = re.match(_SENTENCE_PATTERN, normalized)
    return match.group(1) if match else normalized


def _testthat_test_exists(verify: str, description: str, root: Path) -> bool:
    """Return whether the testthat verify target exists."""
    file_path = _testthat_file(verify)
    group = _first_sentence(description)
    return _file_contains(root, file_path, f'{_TESTTHAT_DESCRIBE_PREFIX}{group}"')


def acceptance_test_exists(criterion: Criterion, root: Path) -> bool:
    """Return whether the criterion's acceptance test exists.

    Args:
        criterion: The criterion to check.
        root: The repository root.

    Returns:
        Whether the acceptance test exists.

    Raises:
        ValueError: If the verify command uses an unsupported runner.
    """
    verify = criterion.verify
    if not verify.startswith(_SUPPORTED_RUNNERS):
        raise ValueError(f"unsupported runner: {verify}")
    if verify.startswith(_PYTEST_PREFIX):
        return _pytest_test_exists(verify, root)
    if verify.startswith(_RSCRIPT_PREFIX):
        return _testthat_test_exists(verify, criterion.description, root)
    _shellspec_file(verify)
    return False


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


def resolve_specs(specs, names):
    """Return the specs named in a qed payload, rejecting unknown names."""
    specs_by_name = {spec.name: spec for spec in specs}
    for name in names:
        if name not in specs_by_name:
            raise ValueError(f"unknown spec name: {name}")
    return specs_by_name


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
