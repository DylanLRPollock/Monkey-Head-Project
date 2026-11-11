"""Cover configuration helpers and compatibility re-export modules."""

from __future__ import annotations

import importlib
import sys
import warnings
from types import ModuleType

import pytest

from huey.settings import RuntimeSettings, _as_bool


def test_environment_settings_normalize_values_and_serialize_paths(tmp_path):
    assert _as_bool(None, default=True) is True
    assert _as_bool(False) is False
    assert _as_bool("  ENABLED ") is True
    assert _as_bool("") is False
    assert _as_bool("no") is False

    settings = RuntimeSettings.from_env(
        {
            "HUEY_ENV": "test",
            "HUEY_HOST": "127.0.0.2",
            "HUEY_PORT": "9080",
            "HUEY_DEBUG": "yes",
            "HUEY_STORAGE_ROOT": str(tmp_path),
            "HUEY_LOG_LEVEL": "debug",
            "HUEY_MODEL_PROVIDER": "local-test",
            "HUEY_MODEL_NAME": "test-model",
            "HUEY_ALLOW_REMOTE_CONTROL": "on",
            "HUEY_HARDWARE_ENABLED": "false",
        }
    )
    payload = settings.to_dict()
    assert payload["port"] == 9080
    assert payload["debug"] is True
    assert payload["storage_root"] == str(tmp_path)
    assert payload["log_level"] == "DEBUG"
    assert payload["allow_remote_control"] is True
    assert payload["hardware_enabled"] is False


def test_api_package_lazy_exports_and_unknown_attribute(monkeypatch):
    package = importlib.import_module("huey.os.api")
    app_module = ModuleType("huey.os.api.app")
    app_module.SCHEDULER = object()
    app_module.app = object()
    app_module.main = lambda: None
    monkeypatch.setitem(sys.modules, "huey.os.api.app", app_module)

    for name in package.__all__:
        value = package.__getattr__(name)
        assert value is getattr(app_module, name)
        assert package.__dict__[name] is value

    with pytest.raises(AttributeError, match="unknown"):
        package.__getattr__("unknown")


def test_api_auth_reexports_legacy_helpers():
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore", message=r"\[huey-env-validation\]", category=RuntimeWarning
        )
        legacy_api = importlib.import_module("huey.memory.PY.api")
    auth = importlib.import_module("huey.os.api.auth")

    for name in auth.__all__:
        assert getattr(auth, name) is getattr(legacy_api, name)


def test_resilience_compatibility_shim_reexports_public_api():
    implementation = importlib.import_module("huey.core.resilience")
    shim = importlib.import_module("huey.os.core.resilience")

    assert shim.__all__ == implementation.__all__
    for name in shim.__all__:
        assert getattr(shim, name) is getattr(implementation, name)
