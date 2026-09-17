#!/usr/bin/env python3
"""
# ---------------------------------------------------------------------------
# Monkey-Head-Project
# Component: HueyOS / Pytest Configuration
# Author: Dylan L.R. Pollock
# Documentation: https://www.dlrp.ca
#
# Philosophy: Breathing new life into old tech.
# ---------------------------------------------------------------------------
"""

"""Pytest configuration and shared fixtures for the Huey test suite.

Responsibilities:

* Put a local ``src/`` checkout (plus ``src/huey/connectors`` and ``vendor``)
  on ``sys.path`` before collection, so tests run against the working tree
  rather than an installed copy.
* Install the Windows selector event-loop policy where the default Proactor
  policy breaks socket-based tests.
* Provide a minimal ``event_loop`` fixture and an ``@pytest.mark.asyncio``
  driver so coroutine tests run without requiring ``pytest-asyncio``.
"""

from __future__ import annotations

import asyncio
import inspect
import sys
from collections.abc import Generator
from pathlib import Path

import pytest

# --- sys.path bootstrap ----------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent
_SRC_PATH = _PROJECT_ROOT / "src"


def _prepend(path: Path) -> None:
    """Put ``path`` at the front of ``sys.path`` if it exists and isn't there."""
    if not path.is_dir():
        return
    resolved = str(path)
    sys.path[:] = [p for p in sys.path if p != resolved]
    sys.path.insert(0, resolved)


def _append(path: Path) -> None:
    """Append ``path`` to ``sys.path`` if it exists and isn't already present."""
    if not path.is_dir():
        return
    resolved = str(path)
    if resolved not in sys.path:
        sys.path.append(resolved)


_prepend(_SRC_PATH)
_append(_SRC_PATH / "huey" / "connectors")
_append(_PROJECT_ROOT / "vendor")


# --- Platform tweaks -------------------------------------------------------


def _install_windows_loop_policy() -> None:
    """Use the selector policy on Windows so socket tests behave.

    The default Proactor policy on Windows cannot drive ``add_reader`` /
    ``add_writer``, which some connector tests rely on. Silently ignore
    environments (e.g. already-configured interpreters) where the policy
    can't be set.
    """
    if not sys.platform.startswith("win"):
        return
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except (AttributeError, NotImplementedError):
        pass


_install_windows_loop_policy()


# --- Event-loop helpers ----------------------------------------------------


def _new_event_loop() -> asyncio.AbstractEventLoop:
    return asyncio.new_event_loop()


def _drain_and_close(loop: asyncio.AbstractEventLoop) -> None:
    """Run pending async-generator / executor shutdown, then close the loop.

    Best-effort: any error during shutdown shouldn't mask the original test
    failure, so exceptions here are swallowed.
    """
    try:
        if not loop.is_closed():
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.run_until_complete(loop.shutdown_default_executor())
    except Exception:
        pass
    finally:
        if not loop.is_closed():
            loop.close()


# --- Fixtures --------------------------------------------------------------


@pytest.fixture
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Yield a fresh event loop and tear it down cleanly.

    Kept as a project fixture (rather than pulled from ``pytest-asyncio``) so
    the test suite has no hard dependency on that plugin.
    """
    loop = _new_event_loop()
    try:
        yield loop
    finally:
        _drain_and_close(loop)


# --- asyncio test driver ---------------------------------------------------


def _make_coro_runner(
    loop: asyncio.AbstractEventLoop,
    func: object,
    kwargs: dict[str, object],
):
    """Return a zero-arg callable that runs ``func(**kwargs)`` on ``loop``."""

    def _run() -> None:
        assert inspect.iscoroutinefunction(func)
        loop.run_until_complete(func(**kwargs))  # type: ignore[misc]

    return _run


@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem: pytest.Function) -> bool:
    """Drive ``@pytest.mark.asyncio`` coroutine tests without pytest-asyncio.

    Returns ``True`` when this hook took responsibility for the call so that
    pytest doesn't try to invoke the coroutine function directly (which would
    just produce a "coroutine was never awaited" warning).
    """
    if pyfuncitem.get_closest_marker("asyncio") is None:
        return False

    func = pyfuncitem.obj
    if not inspect.iscoroutinefunction(func):
        return False

    signature = inspect.signature(func)
    kwargs = {
        name: pyfuncitem.funcargs[name]
        for name in signature.parameters
        if name in pyfuncitem.funcargs
    }

    # Prefer a loop supplied via the ``event_loop`` fixture so the fixture owns
    # teardown; otherwise spin one up for the duration of this single test.
    loop: asyncio.AbstractEventLoop | None = pyfuncitem.funcargs.get("event_loop")
    owns_loop = loop is None
    if loop is None:
        loop = _new_event_loop()

    try:
        loop.run_until_complete(func(**kwargs))
    finally:
        if owns_loop:
            _drain_and_close(loop)

    return True


# --- Marker registration ---------------------------------------------------


def pytest_configure(config: pytest.Config) -> None:
    """Register the ``asyncio`` marker so ``--strict-markers`` stays happy."""
    config.addinivalue_line(
        "markers",
        "asyncio: run the marked coroutine test inside an event loop",
    )