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
    "security/current-risk-register-2026-11-03.md",
    "development/tooling-config-map.md",
    "development/config-reference-audit-2026-11-08.md",
    "testing/test-suite-taxonomy.md",
    "audits/v101.1-repo-control-paths.md",
    "security/privilege-and-identity-audit-2026-11-08.md",
    "release/artifact-audit-2026-11-08.md",
]
