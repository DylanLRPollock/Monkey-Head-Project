"""Tests for the read-only Command Center backend."""

from __future__ import annotations

from huey.apps.command_center.server import (
    create_app,
    get_app_metadata,
    get_launcher_support,
    get_safety_policy,
    get_state_payload,
    get_validation_commands,
)


def test_create_app_exposes_meta_route():
    app = create_app()
    paths = {route.path for route in app.routes}

    assert "/command-center/meta" in paths
    assert get_app_metadata()["mode"] == "read-only"


def test_create_app_exposes_safety_route():
    app = create_app()
    paths = {route.path for route in app.routes}

    assert "/command-center/safety" in paths
    assert get_safety_policy()["mock_only"] is True


def test_create_app_exposes_launcher_route():
    app = create_app()
    paths = {route.path for route in app.routes}
    launcher = get_launcher_support()

    assert "/command-center/launcher" in paths
    assert launcher["mode"] == "safe-bootstrap"
    assert launcher["assets"]["executable"]["present"] is True
    assert launcher["assets"]["source"]["present"] is True
    assert launcher["desktop_shell"]["entry_point"] == "huey.run --manager-ui"
    assert launcher["desktop_shell"]["surface_count"] >= 1
    assert any(
        surface["id"] == "license" for surface in launcher["desktop_shell"]["surfaces"]
    )
    assert any(
        command["option"] == "--doctor" for command in launcher["supported_commands"]
    )


def test_create_app_exposes_validation_route():
    app = create_app()
    paths = {route.path for route in app.routes}
    commands = get_validation_commands()

    assert "/command-center/validation" in paths
    assert commands
    assert all(command["copy_only"] for command in commands)


def test_state_payload_includes_launcher_metadata():
    payload = get_state_payload()

    assert payload["launcher"]["launch_target"] == "HueyOS Command Center"
    assert "No Git mutation" in payload["launcher"]["safety_guarantees"]
    assert any(
        surface["id"] == "command-center" for surface in payload["launcher"]["surfaces"]
    )


def test_backend_does_not_expose_command_execution_route():
    app = create_app()
    paths = {route.path: route.methods for route in app.routes}

    assert "/command-center/execute" not in paths
    assert all(
        "POST" not in (methods or set())
        for path, methods in paths.items()
        if path.startswith("/command-center/")
    )
