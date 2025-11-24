# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Installer module

"""Stub installer used in tests."""

from __future__ import annotations


def run_installer() -> int:
    """Run a no-op installer and report success.

    This stub is intended for use in unit tests and integration tests where
    you want to exercise installer call paths (e.g., from a repair utility)
    without performing any real installation steps such as:

    - Creating virtual environments
    - Installing Python packages
    - Writing configuration files
    - Modifying system paths or user data

    Returns
    -------
    int
        Always returns ``0`` to indicate success.

    Notes
    -----
    In production you would replace this implementation with the real installer
    logic while keeping the same function signature. For example, a future
    implementation might:

    - Validate the runtime environment (Python version, OS, kernel, etc.)
    - Create or migrate configuration directories
    - Initialize SQLite / JSON memory stores
    - Register systemd services or Docker setups for HueyOS
    - Perform sanity checks and return a non-zero exit code on failure

    The test stub keeps this simple and deterministic so that higher-level
    code can be tested without side effects.
    """
    return 0


__all__ = ["run_installer"]
