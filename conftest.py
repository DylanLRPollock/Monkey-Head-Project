"""Pytest hooks providing minimal asyncio support for the tests."""
from __future__ import annotations

import asyncio

import inspect

import pytest


@pytest.fixture
def event_loop() -> asyncio.AbstractEventLoop:
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
    signature = inspect.signature(func)
    kwargs = {
        name: pyfuncitem.funcargs[name]
        for name in signature.parameters
        if name in pyfuncitem.funcargs
    }

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
    return True


def pytest_configure(config: pytest.Config) -> None:  # pragma: no cover - configuration hook
    config.addinivalue_line("markers", "asyncio: run the marked coroutine test inside an event loop")
