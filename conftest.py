# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Conftest module

from __future__ import annotations

import asyncio
import inspect
import sys
from collections.abc import Generator
from pathlib import Path
from typing import cast

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent
_SRC_PATH = _PROJECT_ROOT / "src"
if _SRC_PATH.is_dir() and str(_SRC_PATH) not in sys.path:
    sys.path.insert(0, str(_SRC_PATH))

for _path in (_SRC_PATH / "huey" / "connectors", _PROJECT_ROOT / "vendor"):
    if _path.is_dir() and str(_path) not in sys.path:
        sys.path.append(str(_path))

if sys.platform.startswith("win"):
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except (AttributeError, NotImplementedError):
        pass


@pytest.fixture
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.new_event_loop()
    try:
        yield loop
    finally:
        loop.close()


@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem: pytest.Function) -> bool:
    marker = pyfuncitem.get_closest_marker("asyncio")
    if marker is None:
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

    loop = cast(asyncio.AbstractEventLoop | None, pyfuncitem.funcargs.get("event_loop"))
    manage_loop = False
    if loop is None:
        loop = asyncio.new_event_loop()
        manage_loop = True

    try:
        loop.run_until_complete(func(**kwargs))
    finally:
        if manage_loop:
            loop.close()

    return True


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "asyncio: run the marked coroutine test inside an event loop",
    )
