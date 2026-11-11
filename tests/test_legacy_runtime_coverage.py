"""Deterministic coverage for compact legacy runtime helpers."""

from __future__ import annotations

import importlib
import sys
from types import SimpleNamespace

import pytest


def test_cloud_pyramid_council_votes_and_short_circuit(monkeypatch):
    module = importlib.import_module("huey.memory.PY.cloud_pyramid")
    answers = iter([True, True, False, False, False, True])
    monkeypatch.setattr(module.random, "choice", lambda _options: next(answers))
    assert module.Council(["a", "b", "c"]).vote("proposal") is True
    assert module.Council(["a", "b", "c"]).vote("proposal") is False
    assert module.Council([]).vote("proposal") is True

    pyramid = module.CloudPyramid()
    votes = iter([True, True, False])
    calls = []

    def vote(_council, _proposal):
        calls.append(True)
        return next(votes)

    monkeypatch.setattr(module.Council, "vote", vote)
    assert pyramid.decide("change") is False
    assert len(calls) == 3


@pytest.mark.parametrize("reject_at", range(6))
def test_cloud_pyramid_decision_stops_at_first_rejection(monkeypatch, reject_at):
    module = importlib.import_module("huey.memory.PY.cloud_pyramid")
    pyramid = module.CloudPyramid()
    calls = []

    def vote(_council, _proposal):
        calls.append(True)
        return len(calls) - 1 != reject_at

    monkeypatch.setattr(module.Council, "vote", vote)
    assert pyramid.decide("policy") is False
    assert len(calls) == reject_at + 1


def test_cloud_pyramid_reaches_pinnacle_when_all_councils_approve(monkeypatch):
    module = importlib.import_module("huey.memory.PY.cloud_pyramid")
    pyramid = module.CloudPyramid()
    calls = []
    monkeypatch.setattr(
        module.Council, "vote", lambda _self, _proposal: calls.append(True) or True
    )
    assert pyramid.decide("policy") is True
    assert len(calls) == 6


def test_startup_checks_skip_and_launch_paths(monkeypatch, capsys):
    module = importlib.import_module("huey.memory.PY.startup")
    calls = []
    monkeypatch.setattr(module, "check_os_support", lambda: calls.append("os"))
    monkeypatch.setattr(module, "check_python_version", lambda: calls.append("python"))
    monkeypatch.setattr(module, "system_check", lambda: calls.append("system"))
    monkeypatch.setattr(module.run, "main", lambda: calls.append("main"))

    module.startup()
    assert calls == ["os", "python", "system", "main"]
    calls.clear()
    module.startup(skip_checks=True)
    assert calls == ["main"]
    calls.clear()
    module.startup(dry_run=True)
    assert calls == ["os", "python", "system"]

    def fail_system_check():
        raise RuntimeError("probe failed")

    monkeypatch.setattr(module, "system_check", fail_system_check)
    calls.clear()
    module.startup(dry_run=True)
    assert "System check failed: probe failed" in capsys.readouterr().err
    assert calls == ["os", "python"]
    module.startup(dry_run=False)
    assert calls == ["os", "python", "os", "python", "main"]


def test_startup_main_preserves_unrecognized_arguments(tmp_path, monkeypatch):
    module = importlib.import_module("huey.memory.PY.startup")
    received = []
    monkeypatch.setattr(
        module,
        "startup",
        lambda **kwargs: received.append(kwargs),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["startup.py", "--workdir", str(tmp_path), "--dry-run", "--extra", "value"],
    )
    module.main()
    assert module.os.environ["PYGPT_WORKDIR"] == str(tmp_path.resolve())
    assert sys.argv == ["startup.py", "--extra", "value"]
    assert received == [{"skip_checks": False, "dry_run": True}]

    monkeypatch.setattr(sys, "argv", ["startup.py", "--skip-checks", "--tail"])
    module.main()
    assert sys.argv == ["startup.py", "--tail"]
    assert received[-1] == {"skip_checks": True, "dry_run": False}


def test_legacy_validation_and_linux_service_status(monkeypatch, capsys):
    checks = importlib.import_module("huey.memory.PY.huey_checks")
    assert checks.check_core_data({"processed": True, "input_length": 0}) is True
    assert checks.check_core_data({"processed": False, "input_length": 2}) is False
    assert "not processed" in capsys.readouterr().out
    assert checks.check_core_data([]) is False
    assert "must be a dictionary" in capsys.readouterr().out
    assert checks.check_core_data({"processed": True, "input_length": "2"}) is False
    assert "Invalid input length" in capsys.readouterr().out

    linux = importlib.import_module("huey.memory.PY.huey_linux")
    statuses = iter(["active", "inactive", "failed", "activating"])
    monkeypatch.setattr(
        linux.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            stdout=next(statuses).encode("utf-8"), stderr=b""
        ),
    )
    assert linux.check_linux_service("svc") == "active"
    assert linux.check_linux_service("svc") == "inactive"
    assert linux.check_linux_service("svc") == "failed"
    assert linux.check_linux_service("svc") == "unknown"

    def raise_oserror(*_args, **_kwargs):
        raise OSError("systemctl missing")

    monkeypatch.setattr(linux.subprocess, "run", raise_oserror)
    with pytest.raises(
        OSError, match="Error checking service 'svc': systemctl missing"
    ):
        linux.check_linux_service("svc")
