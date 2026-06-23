#!/usr/bin/env python3
"""Verify the read-only Command Center backend contract."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def assert_imports() -> None:
    import huey.apps.command_center  # noqa: F401
    import huey.gui  # noqa: F401


def assert_routes() -> None:
    from huey.apps.command_center.server import create_app

    app = create_app()
    paths = {route.path: route.methods for route in app.routes}
    required = {
        "/command-center/launcher",
        "/command-center/meta",
        "/command-center/state",
        "/command-center/safety",
        "/command-center/repos",
        "/command-center/phases",
        "/command-center/validation",
        "/command-center/operator-panel",
        "/command-center/v1-runs/sample",
        "/command-center/prompts/phase/{phase_id}",
    }
    missing = sorted(required.difference(paths))
    if missing:
        raise AssertionError(f"Missing routes: {missing}")
    for path, methods in paths.items():
        if not path.startswith("/command-center/"):
            continue
        if "POST" in (methods or set()):
            raise AssertionError(f"Route must remain read-only: {path}")


def assert_launcher_support() -> None:
    from huey.integrations.command_center import get_launcher_support

    payload = get_launcher_support()
    assert payload["mode"] == "safe-bootstrap"
    assert payload["assets"]["executable"]["present"] is True
    assert payload["assets"]["source"]["present"] is True
    assert payload["desktop_shell"]["entry_point"] == "huey.run --manager-ui"
    assert any(surface["id"] == "license" for surface in payload["surfaces"])
    assert "No Git mutation" in payload["safety_guarantees"]


def assert_safety_policy() -> None:
    from huey.gui.safety import default_safety_policy
    from huey.gui.validation import all_validation_commands

    policy = default_safety_policy()
    assert policy.mock_only is True
    assert policy.allow_command_execution is False
    assert policy.allow_task_execution is False
    assert policy.allow_memory_mutation is False
    assert all(command.copy_only for command in all_validation_commands())


def main() -> int:
    try:
        assert_imports()
        assert_routes()
        assert_launcher_support()
        assert_safety_policy()
    except (AssertionError, ImportError, RuntimeError, ValueError) as exc:
        print(f"Command Center contract check failed: {exc}")
        return 1
    print("Command Center contract check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
