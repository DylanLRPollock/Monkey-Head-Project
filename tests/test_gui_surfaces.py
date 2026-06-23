"""Tests for the unified GUI surface catalog."""

from __future__ import annotations

from huey.gui.surfaces import (
    action_lookup,
    default_gui_actions,
    default_gui_sections,
    default_gui_surfaces,
    search_gui_actions,
    section_actions,
)


def test_default_gui_surfaces_include_all_existing_windows() -> None:
    surfaces = {surface.id: surface for surface in default_gui_surfaces()}

    assert "command-center" in surfaces
    assert "graphical-installer" in surfaces
    assert "license" in surfaces
    assert "config-toggles" in surfaces
    assert "simple-chat" in surfaces
    assert "ai-console" in surfaces
    assert "dashboard" in surfaces
    assert surfaces["command-center"].launch_mode == "browser"
    assert surfaces["license"].launch_mode == "dialog"


def test_gui_sections_only_reference_known_actions() -> None:
    actions = default_gui_actions()
    indexed = action_lookup(actions)

    assert indexed["command-center"].function_name == "open_command_center"
    for section in default_gui_sections():
        resolved = section_actions(section, actions)
        assert resolved
        assert all(action.id in indexed for action in resolved)


def test_connectors_and_windows_tab_contains_surface_catalog() -> None:
    sections = [
        section
        for section in default_gui_sections()
        if section.tab_id == "connectors-and-windows"
    ]

    assert sections
    section_ids = {
        action.id for section in sections for action in section_actions(section)
    }
    assert {"command-center", "simple-chat", "ai-console", "dashboard"} <= section_ids


def test_search_gui_actions_supports_navigation_queries() -> None:
    command_center_results = {action.id for action in search_gui_actions("browser")}
    kubernetes_results = {action.id for action in search_gui_actions("kubernetes")}

    assert "command-center" in command_center_results
    assert {"deploy-kubernetes", "scale-deployment", "cleanup-kubernetes"} <= (
        kubernetes_results
    )
