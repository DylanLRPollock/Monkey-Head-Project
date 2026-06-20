"""Tests for legacy GUI availability adapters."""

from __future__ import annotations

from unittest.mock import patch

from huey.gui.legacy_adapters import (
    legacy_ai_tools_gui_available,
    legacy_gui_status,
    legacy_license_gui_available,
)


def test_legacy_gui_status_returns_booleans():
    status = legacy_gui_status()

    assert isinstance(status["license_gui"], bool)
    assert isinstance(status["ai_tools_gui"], bool)


def test_legacy_license_gui_import_check_does_not_launch():
    with (
        patch("huey.gui.legacy_adapters.find_spec", return_value=object()),
        patch("huey.gui.legacy_adapters.import_module") as import_module,
    ):
        assert legacy_license_gui_available() is True
        import_module.assert_not_called()


def test_legacy_ai_tools_gui_import_check_does_not_launch():
    with (
        patch("huey.gui.legacy_adapters.find_spec", return_value=object()),
        patch("huey.gui.legacy_adapters.import_module") as import_module,
    ):
        assert legacy_ai_tools_gui_available() is True
        import_module.assert_not_called()
