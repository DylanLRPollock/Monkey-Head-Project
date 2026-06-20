"""Tests for canonical GUI defaults and validation metadata."""

from huey.gui.defaults import (
    default_migration_phases,
    default_repositories,
    default_validation_commands,
)


def test_default_repositories_include_umbrella_repos():
    full_names = {repo.full_name for repo in default_repositories()}

    assert "DylanLRPollock/Monkey-Head-Project" in full_names
    assert "DylanLRPollock/PyHuey" in full_names
    assert "DylanLRPollock/command-center" in full_names
    assert "DylanLRPollock/dlrp.ca" in full_names


def test_default_phases_include_phase_2_5_and_phase_3():
    phase_ids = {phase.id for phase in default_migration_phases()}

    assert "phase-2-5-pyhuey-connector" in phase_ids
    assert "phase-3-pyhuey-rename" in phase_ids


def test_validation_commands_are_copy_only():
    commands = default_validation_commands()

    assert commands
    assert all(command.copy_only for command in commands)


def test_validation_commands_include_windows_launcher_doctor():
    commands = default_validation_commands()

    assert any(
        command.id == "command-center-launcher-doctor"
        and "HueyOS-Launcher-Setup.exe --doctor" in command.command
        for command in commands
    )
