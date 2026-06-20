"""Shared theme values for every Python GUI surface."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class HueyTheme:
    name: str
    background: str
    panel: str
    panel_alt: str
    text: str
    muted_text: str
    accent: str
    accent_green: str
    warning: str
    danger: str
    success: str
    border: str


_DEFAULT_THEME = HueyTheme(
    name="hueyos-dark-purple",
    background="#141019",
    panel="#1e1726",
    panel_alt="#261d31",
    text="#f8f2ff",
    muted_text="#c8b8d4",
    accent="#7a4fa0",
    accent_green="#00a85a",
    warning="#d19a32",
    danger="#d34a4a",
    success="#00a85a",
    border="#4f3a63",
)


def get_default_theme() -> HueyTheme:
    """Return the canonical HueyOS dark-purple theme."""

    return _DEFAULT_THEME


def as_json(theme: HueyTheme | None = None) -> dict[str, str]:
    """Return serializable theme values."""

    return asdict(theme or get_default_theme())


def as_tk_palette(theme: HueyTheme | None = None) -> dict[str, str]:
    """Return Tkinter-friendly color aliases for legacy and modern GUIs."""

    selected = theme or get_default_theme()
    palette = as_json(selected)
    palette.update(
        {
            "foreground": selected.text,
            "dark_bg": selected.background,
            "light_fg": selected.text,
            "accent_purple": selected.accent,
        }
    )
    return palette


def as_css_variables(theme: HueyTheme | None = None) -> dict[str, str]:
    """Return CSS custom-property values for web UI export."""

    return {
        f"--huey-{key.replace('_', '-')}": value
        for key, value in as_json(theme).items()
    }


__all__ = [
    "HueyTheme",
    "as_css_variables",
    "as_json",
    "as_tk_palette",
    "get_default_theme",
]
