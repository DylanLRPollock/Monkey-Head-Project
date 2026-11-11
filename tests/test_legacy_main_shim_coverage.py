"""Keep the legacy main import path aligned with the maintained Huey module."""

from __future__ import annotations

import importlib
import warnings


def test_legacy_main_shim_reexports_and_delegates():
    implementation = importlib.import_module("huey.main")
    legacy = importlib.import_module("huey.memory.PY.main")

    for name in legacy.__all__:
        assert getattr(legacy, name) is getattr(implementation, name)

    assert legacy.RUNTIME_CONTEXT is implementation.RUNTIME_CONTEXT
    assert legacy.__doc__ == implementation.__doc__


def test_api_app_entrypoint_reexports_and_delegates():
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore", message=r"\[huey-env-validation\]", category=RuntimeWarning
        )
        legacy_api = importlib.import_module("huey.memory.PY.api")
        entrypoint = importlib.import_module("huey.os.api.app")

    for name in entrypoint.__all__:
        assert getattr(entrypoint, name) is getattr(legacy_api, name)
    assert entrypoint._configured_api_tokens is legacy_api._configured_api_tokens
