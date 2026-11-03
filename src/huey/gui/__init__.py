"""Canonical GUI helpers shared across HueyOS surfaces."""

from huey.gui.events import Event, EventBus, EventType
from huey.gui.models import (
    MigrationPhase,
    OperatorPanelState,
    RepoStatus,
    V1RunRecord,
    ValidationCommand,
)
from huey.gui.safety import SafetyPolicy, is_dangerous_action
from huey.gui.state import (
    HueyState,
    MemoryState,
    OperatorState,
    RepositoryState,
    RuntimeState,
    build_default_state,
)
from huey.gui.surfaces import (
    GuiAction,
    GuiActionSection,
    action_lookup,
    default_gui_actions,
    default_gui_sections,
    default_gui_surfaces,
    search_gui_actions,
    section_actions,
)
from huey.gui.theme import HueyTheme, as_qt_stylesheet, as_tk_palette, get_default_theme
from huey.gui.tk import (
    apply_root_chrome,
    apply_ttk_chrome,
    listbox_kwargs,
    primary_button_kwargs,
    text_surface_kwargs,
    tk_palette,
)

__all__ = [
    "Event",
    "EventBus",
    "EventType",
    "GuiAction",
    "GuiActionSection",
    "HueyState",
    "HueyTheme",
    "MemoryState",
    "MigrationPhase",
    "OperatorPanelState",
    "OperatorState",
    "RepoStatus",
    "RepositoryState",
    "RuntimeState",
    "SafetyPolicy",
    "V1RunRecord",
    "ValidationCommand",
    "action_lookup",
    "apply_root_chrome",
    "apply_ttk_chrome",
    "as_qt_stylesheet",
    "as_tk_palette",
    "build_default_state",
    "default_gui_actions",
    "default_gui_sections",
    "default_gui_surfaces",
    "get_default_theme",
    "is_dangerous_action",
    "listbox_kwargs",
    "primary_button_kwargs",
    "search_gui_actions",
    "section_actions",
    "text_surface_kwargs",
    "tk_palette",
]
