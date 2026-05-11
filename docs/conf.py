"""Sphinx configuration for Monkey-Head-Project documentation."""

project = "Monkey-Head-Project"
author = "Dylan L. R. Pollock"

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
]

autodoc_mock_imports = [
    "torch",
    "torchaudio",
    "transformers",
    "sounddevice",
    "faster_whisper",
]

templates_path = ["_templates"]
exclude_patterns = ["_build"]

html_theme = "alabaster"

myst_enable_extensions = ["colon_fence"]

include_patterns = [
    "index.rst",
    "development/v101.1-namespace-migration.md",
    "security/security-hardening-status.md",
    "audits/v101.1-repo-control-paths.md",
]
