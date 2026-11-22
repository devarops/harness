"""The harness TDD entry point."""

from pathlib import Path

from harness import prompts, qed
from harness.spec import acceptance_test_exists, import_specs, is_spec_present

_LOG_NAME = "harness.log"
_PROMPT_DIR = Path.home() / ".config" / "opencode" / "commands"
_CONTAINER_SUFFIX = "_dev"


def tdd() -> None:
    """Run the ATDD/TDD loop against the current repository."""
    root = Path.cwd()
    if not is_spec_present(root):
        _abort("Error: no specs/*.spec.toml found at the repository root.")
    if not _ignores_log(root):
        _abort("Error: .gitignore must ignore harness.log.")
    _run_pass(root)


def _run_pass(root: Path) -> None:
    """Run acceptance once and route its failure."""
    container = f"{root.name}{_CONTAINER_SUFFIX}"
    prompts.run_prompt(_PROMPT_DIR / "atdd-acceptance.md")
    report = qed.verify(container, root, import_specs(root))
    failed = report.failed
    if len(failed) > 1:
        _abort("Error: more than one unskipped criterion fails.")
    if not failed:
        return
    name, description = failed[0]
    criterion = next(
        item for item in report.specs[name].criteria if item.description == description
    )
    if not acceptance_test_exists(criterion, root):
        prompts.run_prompt(_PROMPT_DIR / "atdd-red.md")


def _abort(message: str) -> None:
    """Print the message and stop the run."""
    print(message)
    raise SystemExit(1)


def _ignores_log(root: Path) -> bool:
    """Return whether the target gitignore names the run log."""
    ignore = root / ".gitignore"
    return ignore.is_file() and _LOG_NAME in ignore.read_text()
