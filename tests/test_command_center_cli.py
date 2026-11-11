"""Tests for the Command Center browser launcher helpers."""

from __future__ import annotations

from pathlib import Path

from huey.apps.command_center import cli


def test_local_frontend_path_detects_bundled_dist(tmp_path: Path) -> None:
    dist = tmp_path / "integrations" / "command-center" / "dist"
    dist.mkdir(parents=True)
    index = dist / "index.html"
    index.write_text("<html></html>", encoding="utf-8")

    assert cli.local_frontend_path(tmp_path) == index
    assert cli.resolve_frontend_url(tmp_path) == index.resolve().as_uri()


def test_resolve_frontend_url_prefers_configured_env(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("HUEY_COMMAND_CENTER_FRONTEND", "https://example.invalid/ui")
    dist = tmp_path / "integrations" / "command-center" / "dist"
    dist.mkdir(parents=True)
    (dist / "index.html").write_text("<html></html>", encoding="utf-8")

    assert cli.resolve_frontend_url(tmp_path) == "https://example.invalid/ui"


def test_open_command_center_uses_resolved_url(monkeypatch) -> None:
    monkeypatch.setattr(
        cli, "resolve_frontend_url", lambda project_root=None: "file:///tmp/index.html"
    )
    opened: dict[str, str] = {}
    monkeypatch.setattr(cli, "open_browser", lambda url: opened.setdefault("url", url))

    assert cli.open_command_center() == "file:///tmp/index.html"
    assert opened["url"] == "file:///tmp/index.html"


def test_cli_defaults_and_external_frontend_fallback(monkeypatch) -> None:
    assert cli.parse_args([]).host == "127.0.0.1"
    assert cli.parse_args([]).port == 1996
    assert cli.parse_args(["--host", "0.0.0.0", "--port", "2000", "--reload"]).reload

    monkeypatch.setattr(cli, "_project_root", lambda: None)
    monkeypatch.setattr(
        cli, "command_center_frontend_url", lambda: "https://static.example/ui"
    )
    assert cli.local_frontend_path() is None
    assert cli.resolve_frontend_url() == "https://static.example/ui"


def test_cli_open_timer_and_server_dispatch(monkeypatch) -> None:
    timers = []
    servers = []

    class Timer:
        def __init__(self, delay, callback):
            self.delay = delay
            self.callback = callback

        def start(self):
            timers.append(self)

    monkeypatch.setattr(cli.threading, "Timer", Timer)
    monkeypatch.setattr(
        cli, "run_server", lambda *args, **kwargs: servers.append((args, kwargs))
    )

    assert cli.main(["--host", "0.0.0.0", "--port", "2100", "--reload", "--open"]) == 0
    assert servers == [(("0.0.0.0", 2100), {"reload": True})]
    assert len(timers) == 1
    assert timers[0].delay == 1.0


def test_run_server_uses_uvicorn(monkeypatch) -> None:
    import sys
    from types import ModuleType

    calls = []
    uvicorn = ModuleType("uvicorn")
    uvicorn.run = lambda *args, **kwargs: calls.append((args, kwargs))
    monkeypatch.setitem(sys.modules, "uvicorn", uvicorn)

    cli.run_server("127.0.0.1", 1996, reload=True)

    assert calls == [
        (
            ("huey.apps.command_center.server:app",),
            {"host": "127.0.0.1", "port": 1996, "reload": True},
        )
    ]
