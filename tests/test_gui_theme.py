"""Tests for the canonical GUI theme helpers."""

from huey.gui.theme import as_css_variables, as_tk_palette, get_default_theme


def test_default_theme_has_required_colors():
    theme = get_default_theme()

    assert theme.background.startswith("#")
    assert theme.panel.startswith("#")
    assert theme.text.startswith("#")
    assert theme.accent.startswith("#")


def test_tk_palette_contains_legacy_keys():
    palette = as_tk_palette()

    assert palette["background"]
    assert palette["text"]
    assert palette["accent"]
    assert palette["dark_bg"] == palette["background"]
    assert palette["light_fg"] == palette["text"]
    assert palette["accent_purple"] == palette["accent"]


def test_css_variables_are_prefixed():
    css_variables = as_css_variables()

    assert css_variables
    assert all(key.startswith("--huey-") for key in css_variables)
