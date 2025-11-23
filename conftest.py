# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Conftest module

"""Pytest configuration and hooks for HueyOS.

This module provides:

* A stable import path so tests can import from ``src`` without installing the
  package.
* A dedicated asyncio event-loop fixture for tests that need it.
* A custom ``pytest_pyfunc_call`` hook that runs tests marked with
  ``@pytest.mark.asyncio`` inside an event loop without requiring additional
  plugins.
"""

from __future__ import annotations

import asyncio
import inspect
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Test import path bootstrap
# ---------------------------------------------------------------------------

# Ensure the ``src`` directory is importable without requiring installation.
_PROJECT_ROOT = Path(__file__).resolve().parent
_SRC_PATH = _PROJECT_ROOT / "src"
if str(_SRC_PATH) not in sys.path:
    sys.path.insert(0, str(_SRC_PATH))


# ---------------------------------------------------------------------------
# Asyncio event-loop policy (especially important on Windows)
# ---------------------------------------------------------------------------

# On Windows, prefer the selector event loop policy for better compatibility
# with typical networking and test scenarios. On non-Windows platforms, this
# is a no-op.
if sys.platform.startswith("win"):
    try:
        # ``WindowsSelectorEventLoopPolicy`` is generally more compatible with
        # third-party libraries than the Proactor policy in test environments.
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except (AttributeError, NotImplementedError):
        # If for some reason this policy is unavailable, silently fall back to
        # the default policy.
        pass


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def event_loop() -> asyncio.AbstractEventLoop:
    """Per-test asyncio event loop.

    This fixture creates a fresh event loop for each test that depends on it,
    ensuring that tasks and state are not leaked between tests. It is also used
    by the custom ``pytest_pyfunc_call`` hook when a test is marked with
    ``@pytest.mark.asyncio`` but does not explicitly request an ``event_loop``
    fixture.

    Usage examples
    --------------

    * Explicit loop injection:

      .. code-block:: python

         @pytest.mark.asyncio
         async def test_example(event_loop):
             # You can use the loop directly if you want finer control
             task = event_loop.create_task(some_coroutine())
             await task

    * Implicit loop management:

      .. code-block:: python

         @pytest.mark.asyncio
         async def test_example():
             # The hook will still provide an event loop even without the
             # explicit fixture in the signature.
             await some_coroutine()
    """
    loop = asyncio.new_event_loop()
    try:
        yield loop
    finally:
        loop.close()


# ---------------------------------------------------------------------------
# Hooks
# ---------------------------------------------------------------------------


@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem: pytest.Function) -> bool:
    """Execute tests marked with ``@pytest.mark.asyncio`` inside an event loop.

    This hook looks for the ``asyncio`` marker and, if present, treats the
    underlying test function as a coroutine to be run with ``run_until_complete``.

    Behavior
    --------
    * If the test is **not** marked with ``@pytest.mark.asyncio``, this hook
      returns ``False`` and pytest executes the test normally.
    * If the test **is** marked, the hook:
        - Resolves its arguments from ``pyfuncitem.funcargs``.
        - Looks for an existing ``event_loop`` fixture.
        - If none is found, creates a temporary loop for that test.
        - Runs the coroutine to completion.
        - Cleans up the temporary loop if it created one.

    This avoids pulling in additional asyncio plugins while still allowing you
    to write idiomatic async tests.
    """
    marker = pyfuncitem.get_closest_marker("asyncio")
    if marker is None:
        # Not an asyncio test; let pytest handle it normally.
        return False

    func = pyfuncitem.obj

    # If somehow the marker is present on a non-async function, do nothing and
    # let pytest error in the usual way rather than silently swallowing it.
    if not inspect.iscoroutinefunction(func):
        return False

    # Build the keyword arguments for the test from the available fixtures.
    signature = inspect.signature(func)
    kwargs = {
        name: pyfuncitem.funcargs[name]
        for name in signature.parameters
        if name in pyfuncitem.funcargs
    }

    # Try to reuse a provided event_loop fixture; otherwise create a temporary one.
    loop = pyfuncitem.funcargs.get("event_loop")
    manage_loop = False
    if loop is None:
        loop = asyncio.new_event_loop()
        manage_loop = True

    try:
        loop.run_until_complete(func(**kwargs))
    finally:
        if manage_loop:
            loop.close()

    # Returning True tells pytest that we've executed the test ourselves.
    return True


def pytest_configure(config: pytest.Config) -> None:  # pragma: no cover - config hook
    """Register custom markers and global configuration for pytest.

    Currently, this registers the ``asyncio`` marker so that pytest does not
    complain about an unknown marker when running the test suite.

    You can extend this function with additional global configuration or
    marker registrations as the test suite grows.
    """
    config.addinivalue_line(
        "markers",
        "asyncio: run the marked coroutine test inside an event loop",
    )
