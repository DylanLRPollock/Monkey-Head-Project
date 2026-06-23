"""Copy-only validation command registry for dashboard and operator flows."""

from __future__ import annotations

from huey.gui.models import ValidationCommand


def monkey_head_validation_commands() -> list[ValidationCommand]:
    """Return Monkey-Head-Project validation commands."""

    return [
        ValidationCommand(
            id="stale-platform-strings",
            repo="DylanLRPollock/Monkey-Head-Project",
            command="python scripts/repo/check_stale_platform_strings.py",
            purpose="Catch stale platform labels and renamed surfaces.",
            expected_result="Script prints a pass message and exits with code 0.",
            risk="low",
            phase_id="phase-2-huey-os-canonical",
        ),
        ValidationCommand(
            id="repo-drift",
            repo="DylanLRPollock/Monkey-Head-Project",
            command="python scripts/repo/check_repo_drift.py",
            purpose="Detect current-facing repository drift strings.",
            expected_result="Script prints 'Repo drift check passed.'",
            risk="medium",
            phase_id="phase-2-huey-os-canonical",
        ),
        ValidationCommand(
            id="legacy-hueyos-imports",
            repo="DylanLRPollock/Monkey-Head-Project",
            command="python scripts/repo/check_legacy_hueyos_imports.py",
            purpose="Prevent new legacy namespace import regressions.",
            expected_result="Script exits with code 0 and reports no violations.",
            risk="medium",
            phase_id="phase-2-huey-os-canonical",
        ),
        ValidationCommand(
            id="dependency-sync",
            repo="DylanLRPollock/Monkey-Head-Project",
            command="python scripts/repo/check_dependency_sync.py",
            purpose="Verify pyproject, requirements, and constraints stay aligned.",
            expected_result="Dependency sync check passed.",
            risk="high",
            phase_id="phase-2-huey-os-canonical",
        ),
        ValidationCommand(
            id="active-dependency-surface",
            repo="DylanLRPollock/Monkey-Head-Project",
            command="python scripts/repo/check_active_dependency_surface.py",
            purpose="Report duplicate, orphaned, and inactive direct dependencies.",
            expected_result="Script exits 0 when the active dependency surface is coherent.",
            risk="high",
            phase_id="phase-2-huey-os-canonical",
        ),
        ValidationCommand(
            id="archived-dependency-snapshots",
            repo="DylanLRPollock/Monkey-Head-Project",
            command="python scripts/repo/check_archived_dependency_snapshots.py",
            purpose="Validate archived dependency manifests and known-good snapshots.",
            expected_result="Script exits 0 when archived snapshots are present and readable.",
            risk="medium",
            phase_id="phase-2-huey-os-canonical",
        ),
        ValidationCommand(
            id="black-check",
            repo="DylanLRPollock/Monkey-Head-Project",
            command="python -m black --check src tests scripts conftest.py",
            purpose="Verify formatting stays stable.",
            expected_result="Black exits with code 0.",
            risk="low",
        ),
        ValidationCommand(
            id="isort-check",
            repo="DylanLRPollock/Monkey-Head-Project",
            command="python -m isort --check-only src tests scripts conftest.py",
            purpose="Verify import ordering stays stable.",
            expected_result="isort exits with code 0.",
            risk="low",
        ),
        ValidationCommand(
            id="ruff-check",
            repo="DylanLRPollock/Monkey-Head-Project",
            command="python -m ruff check src tests scripts conftest.py",
            purpose="Run the primary Python lint surface.",
            expected_result="ruff exits with code 0.",
            risk="medium",
        ),
        ValidationCommand(
            id="flake8-check",
            repo="DylanLRPollock/Monkey-Head-Project",
            command=(
                "python -m flake8 --exclude=src/huey/connectors/pyhuey "
                "src tests scripts conftest.py"
            ),
            purpose="Run legacy style checks that still guard parts of the tree.",
            expected_result="flake8 exits with code 0.",
            risk="medium",
        ),
        ValidationCommand(
            id="pytest-all",
            repo="DylanLRPollock/Monkey-Head-Project",
            command="python -m pytest -q",
            purpose="Run the repository test suite.",
            expected_result="pytest exits with code 0.",
            risk="high",
        ),
    ]


def pyhuey_validation_commands() -> list[ValidationCommand]:
    """Return PyHuey validation commands."""

    return [
        ValidationCommand(
            id="pyhuey-status",
            repo="DylanLRPollock/PyHuey",
            command="python -m huey.pyhuey_integration",
            purpose="Inspect PyHuey discovery and source resolution status.",
            expected_result="Command prints source candidates without mutating anything.",
            risk="low",
            phase_id="phase-2-5-pyhuey-connector",
        ),
    ]


def command_center_validation_commands() -> list[ValidationCommand]:
    """Return Command Center validation commands."""

    return [
        ValidationCommand(
            id="command-center-contract",
            repo="DylanLRPollock/Monkey-Head-Project",
            command="python scripts/check_command_center_contract.py",
            purpose="Verify the read-only backend exposes the expected API contract.",
            expected_result="Script exits 0 and confirms route and safety guarantees.",
            risk="high",
            phase_id="phase-5-v1-run-dashboard",
        ),
        ValidationCommand(
            id="command-center-seed",
            repo="DylanLRPollock/Monkey-Head-Project",
            command=(
                "python scripts/export_command_center_seed.py "
                "--output docs/tools/command-center-seed.json"
            ),
            purpose="Export canonical seed data for the separate frontend app.",
            expected_result="Script writes a seed JSON file without mutating runtime state.",
            risk="low",
            phase_id="phase-5-v1-run-dashboard",
        ),
        ValidationCommand(
            id="command-center-launcher-doctor",
            repo="DylanLRPollock/Monkey-Head-Project",
            command=(
                r".\src\huey\platform\installers\windows\launcher"
                r"\HueyOS-Launcher-Setup.exe --doctor"
            ),
            purpose=(
                "Generate the local Windows launcher doctor report for Command "
                "Center bootstrap prerequisites."
            ),
            expected_result=(
                r"The launcher writes %LOCALAPPDATA%\HueyOS\doctor-report.txt "
                "and opens it in Notepad without mutating the repo or shell state."
            ),
            risk="low",
            phase_id="phase-5-v1-run-dashboard",
            notes=(
                r"Windows-only. Run "
                r".\src\huey\platform\installers\windows\launcher"
                r"\HueyOS-Launcher-Setup.exe --set-repo "
                r"L:\Monkey-Head-Project "
                "once before using --launch or repo-aware doctor checks."
            ),
        ),
        ValidationCommand(
            id="command-center-backend-tests",
            repo="DylanLRPollock/Monkey-Head-Project",
            command=(
                "python -m pytest -q tests/test_command_center_backend.py "
                "tests/test_legacy_gui_adapters.py"
            ),
            purpose="Exercise the read-only backend and legacy GUI bridges.",
            expected_result="pytest exits with code 0.",
            risk="medium",
            phase_id="phase-5-v1-run-dashboard",
        ),
    ]


def all_validation_commands() -> list[ValidationCommand]:
    """Return every registered validation command."""

    commands = (
        monkey_head_validation_commands()
        + pyhuey_validation_commands()
        + command_center_validation_commands()
    )
    return commands


def commands_by_repo() -> dict[str, list[ValidationCommand]]:
    """Group validation commands by repository."""

    grouped: dict[str, list[ValidationCommand]] = {}
    for command in all_validation_commands():
        grouped.setdefault(command.repo, []).append(command)
    return grouped


def get_command(command_id: str) -> ValidationCommand:
    """Lookup a validation command by its identifier."""

    for command in all_validation_commands():
        if command.id == command_id:
            return command
    raise KeyError(f"Unknown validation command: {command_id}")


__all__ = [
    "all_validation_commands",
    "command_center_validation_commands",
    "commands_by_repo",
    "get_command",
    "monkey_head_validation_commands",
    "pyhuey_validation_commands",
]
