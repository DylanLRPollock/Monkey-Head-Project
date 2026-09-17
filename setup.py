# ---------------------------------------------------------------------------
# Monkey-Head-Project
# Component: HueyOS / Build Environment
# Author: Dylan L.R. Pollock
# Documentation: https://www.dlrp.ca
#
# Philosophy: Breathing new life into old tech.
# ---------------------------------------------------------------------------

"""Compatibility ``setup.py`` for editable installs and legacy tooling.

This file exists *only* so that ``pip install -e .`` and older tools that
still shell out to ``setup.py`` keep working. All project metadata lives in
``pyproject.toml``; do not add configuration here.

The checks below fail fast with an actionable message instead of letting
setuptools emit a confusing traceback or silently build an empty package.
"""

from __future__ import annotations

import sys
from pathlib import Path

# --- Requirements ----------------------------------------------------------

MIN_PYTHON = (3, 9)
# setuptools 61 was the first release able to read [project] from pyproject.toml.
MIN_SETUPTOOLS = (61, 0, 0)

ROOT = Path(__file__).resolve().parent
PYPROJECT = ROOT / "pyproject.toml"

# Commands removed from modern setuptools; we warn rather than hard-fail.
LEGACY_COMMANDS = {"install", "develop", "easy_install", "upload", "register"}


class SetupError(SystemExit):
    """Exit with a clear, actionable message instead of a traceback."""

    def __init__(self, message: str, hint: str | None = None) -> None:
        lines = [f"error: {message}"]
        if hint:
            lines.append(f"hint:  {hint}")
        super().__init__("\n".join(lines))


# --- Checks ----------------------------------------------------------------


def _check_python() -> None:
    if sys.version_info < MIN_PYTHON:
        raise SetupError(
            f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ is required, but you are "
            f"running {sys.version.split()[0]}.",
            "Install a newer interpreter or activate a virtualenv.",
        )


def _parse_version(raw: str) -> tuple[int, int, int] | None:
    """Best-effort ``"61.0.1.dev0"`` -> ``(61, 0, 1)``. Returns None if unparsable."""
    parts: list[int] = []
    for chunk in raw.split("."):
        digits = ""
        for char in chunk:
            if not char.isdigit():
                break
            digits += char
        if not digits:
            break
        parts.append(int(digits))
    if not parts:
        return None
    return tuple((parts + [0, 0, 0])[:3])  # type: ignore[return-value]


def _check_setuptools_version() -> None:
    try:
        from importlib.metadata import PackageNotFoundError, version
    except ImportError:  # pragma: no cover - only on very old interpreters
        return
    try:
        raw = version("setuptools")
    except PackageNotFoundError:  # pragma: no cover - vendored setuptools
        return

    parsed = _parse_version(raw)
    if parsed is not None and parsed < MIN_SETUPTOOLS:
        want = ".".join(str(p) for p in MIN_SETUPTOOLS)
        raise SetupError(
            f"setuptools {want}+ is required (found {raw}).",
            "python -m pip install --upgrade 'setuptools>=61'",
        )


def _load_setuptools():
    """Import and return ``setuptools.setup``, or raise a helpful error."""
    try:
        from setuptools import setup
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise SetupError(
            "setuptools is not installed in this interpreter.",
            "python -m pip install --upgrade setuptools",
        ) from exc

    _check_setuptools_version()
    return setup


def _declares_project_metadata(text: str) -> bool:
    """True if pyproject.toml has a [project] or [tool.setuptools] table."""
    try:
        import tomllib
    except ModuleNotFoundError:  # Python < 3.11: cheap textual fallback
        return "[project]" in text or "[tool.setuptools" in text

    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise SetupError(f"{PYPROJECT.name} is not valid TOML: {exc}") from exc

    return "project" in data or "setuptools" in data.get("tool", {})


def _check_pyproject() -> None:
    if not PYPROJECT.is_file():
        raise SetupError(
            f"{PYPROJECT.name} not found next to setup.py ({ROOT}).",
            "All metadata lives in pyproject.toml; run setup.py from the "
            "project root or restore the file.",
        )

    try:
        text = PYPROJECT.read_text(encoding="utf-8")
    except OSError as exc:
        raise SetupError(f"could not read {PYPROJECT}: {exc}") from exc

    if not text.strip():
        raise SetupError(f"{PYPROJECT} is empty.")

    if not _declares_project_metadata(text):
        raise SetupError(
            f"{PYPROJECT} declares neither [project] nor [tool.setuptools].",
            "Without metadata, setup() would build an empty distribution.",
        )


def _warn_legacy_invocation() -> None:
    invoked = {arg for arg in sys.argv[1:] if not arg.startswith("-")}
    deprecated = invoked & LEGACY_COMMANDS
    if not deprecated:
        return

    names = ", ".join(sorted(deprecated))
    print(
        f"warning: `setup.py {names}` is deprecated and will be removed.\n"
        f"         use `python -m pip install .` (or `-e .`) instead.",
        file=sys.stderr,
    )


# --- Entry point -----------------------------------------------------------


def main() -> int:
    try:
        _check_python()
        setup = _load_setuptools()
        _check_pyproject()
        _warn_legacy_invocation()
        setup()
    except KeyboardInterrupt:
        print("\nsetup.py: interrupted", file=sys.stderr)
        return 130
    except BrokenPipeError:  # e.g. `setup.py --help | head`
        try:
            sys.stdout.close()
        except Exception:
            pass
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())