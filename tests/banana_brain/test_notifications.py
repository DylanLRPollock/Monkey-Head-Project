"""Tests for notification validation, dispatch, and backend failure paths."""

from __future__ import annotations

import asyncio
import json

import pytest

from huey.banana_brain.notifications import (
    DesktopBackend,
    FileBackend,
    Kinds,
    LogBackend,
    Notification,
    NotificationLevel,
    Notifier,
    WebhookBackend,
    _parse_level,
)


def note(level=NotificationLevel.INFO, **changes):
    values = {
        "id": "n1",
        "at": 1.0,
        "level": level,
        "title": "title",
        "message": "message",
        "details": {},
        "kind": None,
        "key": None,
    }
    values.update(changes)
    return Notification(**values)


def test_levels_aliases_and_notification_serialization():
    assert _parse_level("OK") is NotificationLevel.INFO
    assert _parse_level("warning") is NotificationLevel.WARN
    assert _parse_level("crit") is NotificationLevel.CRITICAL
    assert _parse_level(NotificationLevel.ERROR) is NotificationLevel.ERROR
    with pytest.raises(ValueError, match="unknown notification level"):
        _parse_level("verbose")
    assert NotificationLevel.CRITICAL.label() == "critical"
    assert note(kind=Kinds.THERMAL).to_dict()["kind"] == "thermal"


@pytest.mark.asyncio
async def test_log_backend_level_routing(caplog):
    caplog.set_level("DEBUG", logger="banana_brain.notifications")
    backend = LogBackend(NotificationLevel.INFO)
    for level in NotificationLevel:
        await backend.send(note(level, details={"gpu": 0}))
    await backend.close()
    assert "notification details" in caplog.text
    assert "title: message" in caplog.text


@pytest.mark.asyncio
async def test_file_backend_appends_and_disables_after_failure(tmp_path, monkeypatch):
    path = tmp_path / "nested" / "notifications.jsonl"
    backend = FileBackend(path, min_level=NotificationLevel.INFO)
    await backend.send(note())
    await backend.send(note(title="second"))
    await backend.close()
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert [row["title"] for row in rows] == ["title", "second"]
    assert backend._handle is None

    def fail_open(*args, **kwargs):
        raise OSError("disk full")

    broken = FileBackend(tmp_path / "broken", min_level=NotificationLevel.INFO)
    monkeypatch.setattr("builtins.open", fail_open)
    await broken.send(note())
    assert broken._failed is True
    await broken.send(note())
    await broken.close()


@pytest.mark.asyncio
async def test_desktop_backend_missing_binary_and_failure_paths(  # noqa: C901,RUF100
    monkeypatch,
):
    monkeypatch.setattr("huey.banana_brain.notifications.shutil.which", lambda _: None)
    missing = DesktopBackend(NotificationLevel.INFO)
    await missing.send(note())
    await missing.close()

    monkeypatch.setattr(
        "huey.banana_brain.notifications.shutil.which", lambda _: "/bin/notify-send"
    )
    backend = DesktopBackend(NotificationLevel.INFO, timeout_ms=12)
    args_seen = []

    class Proc:
        returncode = 0

        async def communicate(self):
            return b"", b""

    async def spawn(*args, **kwargs):
        args_seen.extend(args)
        return Proc()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", spawn)
    await backend.send(
        note(
            NotificationLevel.WARN,
            details={str(i): "x" * 200 for i in range(6)},
        )
    )
    assert "normal" in args_seen
    body = args_seen[-1]
    assert len(body) <= 512

    async def not_found(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(asyncio, "create_subprocess_exec", not_found)
    await backend.send(note())
    assert backend._binary is None

    backend = DesktopBackend(NotificationLevel.INFO)
    backend._binary = "/bin/notify-send"

    class Process:
        def __init__(self, code=0):
            self.returncode = code
            self.killed = False

        async def communicate(self):
            return b"", b"no desktop"

        def kill(self):
            self.killed = True

    process = Process(1)

    async def spawn_failure(*_args, **_kwargs):
        return process

    monkeypatch.setattr(asyncio, "create_subprocess_exec", spawn_failure)
    await backend.send(note(NotificationLevel.ERROR))
    assert backend._availability_warned is True
    assert backend._binary is None

    backend._binary = "/bin/notify-send"

    async def spawn_timeout(*_args, **_kwargs):
        class TimeoutProcess(Process):
            async def communicate(self):
                raise TimeoutError

        return TimeoutProcess()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", spawn_timeout)
    await backend.send(note())

    async def spawn_error(*_args, **_kwargs):
        raise RuntimeError("spawn failed")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", spawn_error)
    await backend.send(note())


@pytest.mark.asyncio
async def test_webhook_session_auth_http_errors_timeout_and_close(monkeypatch):
    backend = WebhookBackend(
        "https://example.invalid/hook",
        token="secret",
        min_level=NotificationLevel.ERROR,
        timeout_s=2,
    )
    captured = {}

    class Response:
        status = 401

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def text(self):
            return "bad token"

    class Session:
        closed = False

        def post(self, url, *, json):
            captured.update(url=url, json=json)
            return Response()

        async def close(self):
            self.closed = True

    session = Session()

    def create_session(**kwargs):
        captured["headers"] = kwargs["headers"]
        return session

    monkeypatch.setattr(
        "huey.banana_brain.notifications.aiohttp.ClientSession", create_session
    )
    assert await backend._ensure_session() is session
    assert captured["headers"]["Authorization"] == "Bearer secret"
    await backend.send(note(NotificationLevel.ERROR))
    assert captured["json"]["id"] == "n1"
    await backend.send(note(NotificationLevel.ERROR))
    assert backend._auth_failure_warned is True
    await backend.close()
    assert session.closed is True
    assert backend._session is None

    class TimeoutSession(Session):
        def post(self, *args, **kwargs):
            raise TimeoutError

    monkeypatch.setattr(
        backend, "_ensure_session", lambda: asyncio.sleep(0, result=TimeoutSession())
    )
    await backend.send(note())

    class BrokenSession(Session):
        def post(self, *_args, **_kwargs):
            raise RuntimeError("network down")

    monkeypatch.setattr(
        backend, "_ensure_session", lambda: asyncio.sleep(0, result=BrokenSession())
    )
    await backend.send(note())
    await backend.close()


@pytest.mark.asyncio
async def test_file_backend_close_error_and_notifier_timeouts(monkeypatch, tmp_path):
    class BrokenHandle:
        def write(self, _value):
            pass

        def flush(self):
            pass

        def close(self):
            raise OSError("close failed")

    file_backend = FileBackend(tmp_path / "events", min_level=NotificationLevel.INFO)
    file_backend._handle = BrokenHandle()
    await file_backend.close()
    assert file_backend._handle is None

    notifier = Notifier({"notifications_shutdown_grace_seconds": 0.01})

    class Slow:
        name = "slow"
        min_level = NotificationLevel.INFO

        async def send(self, _item):
            raise TimeoutError

        async def close(self):
            pass

    notifier._backends = [Slow()]
    await notifier._deliver(note())
    assert notifier.get_stats()["backend_failures"] == 1
    await notifier.start()
    await notifier.notify("info", "pending", "body")
    await notifier.stop()
    assert notifier._queue is None


@pytest.mark.asyncio
async def test_notifier_deduplicates_filters_overflow_and_delivers():
    notifier = Notifier(
        {"notifications_queue_maxsize": 1, "notifications_cooldown_seconds": 30}
    )
    notifier._queue = asyncio.Queue(maxsize=1)
    backend = notifier._backends[0]
    sent = []

    async def send(item):
        sent.append(item)

    backend.send = send

    await notifier.notify("ok", "first", "body", kind="event", key="ID")
    await notifier.notify("warn", "repeat", "body", kind="event", key="id")
    assert notifier.get_stats()["dropped_cooldown"] == 1
    await notifier.notify("bad-level", "ignored", "body")
    assert notifier.get_stats()["queue_depth"] == 1
    await notifier.notify("critical", "next", "body")
    assert notifier.get_stats()["dropped_overflow"] == 1
    assert notifier.get_stats()["queue_depth"] == 1
    notifier._queue.get_nowait()
    notifier._queue.task_done()
    notifier._queue = None

    await notifier.start()
    with pytest.raises(RuntimeError, match="already started"):
        await notifier.start()
    await notifier.notify("warning", "worker", "body")
    await asyncio.wait_for(notifier._queue.join(), timeout=1)
    assert len(sent) == 1
    assert notifier.get_stats()["delivered"] == 1
    await notifier.stop()
    assert notifier._queue is None
    # Not running falls back to the log backend and closes cleanly twice.
    await notifier.notify("info", "fallback", "body")
    await notifier.stop()


@pytest.mark.asyncio
async def test_notifier_disabled_and_backend_failures(monkeypatch):
    disabled = Notifier({"notifications_enabled": False})
    await disabled.start()
    await disabled.notify("info", "ignored", "message")
    await disabled.stop()
    assert disabled.get_stats()["enqueued"] == 0

    notifier = Notifier(
        {"notifications_enabled": True, "notifications_shutdown_grace_seconds": 0.01}
    )

    class Broken:
        name = "broken"
        min_level = NotificationLevel.INFO

        async def send(self, item):
            raise RuntimeError("offline")

        async def close(self):
            raise RuntimeError("close failed")

    notifier._backends = [Broken()]
    await notifier.start()
    await notifier.notify("info", "fails", "message")
    await asyncio.wait_for(notifier._queue.join(), timeout=1)
    assert notifier.get_stats()["backend_failures"] == 1
    await notifier.stop()


@pytest.mark.asyncio
async def test_delivery_filters_backend_levels_and_records_timeout():
    notifier = Notifier({})

    class BackendStub:
        name = "critical-only"
        min_level = NotificationLevel.CRITICAL

        async def send(self, _notification):
            return None

        async def close(self):
            return None

    backend = BackendStub()
    notifier._backends = [backend]
    await notifier._deliver(note(NotificationLevel.INFO))
    assert notifier.get_stats()["delivered"] == 0

    backend.min_level = NotificationLevel.INFO

    async def timeout(_notification):
        raise TimeoutError

    backend.send = timeout
    await notifier._deliver(note(NotificationLevel.INFO))
    assert notifier.get_stats()["backend_failures"] == 1
    assert notifier.get_stats()["delivered"] == 0


def test_backend_configuration_parsing(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "huey.banana_brain.notifications.shutil.which", lambda _: "/bin/notify-send"
    )
    notifier = Notifier(
        {
            "notifications_desktop_enabled": True,
            "notifications_webhook_url": "https://example.invalid/hook",
            "notifications_webhook_token": "token",
            "notifications_file_path": str(tmp_path / "events.jsonl"),
            "notifications_min_level_log": "warning",
            "notifications_min_level_desktop": "error",
            "notifications_min_level_webhook": "critical",
            "notifications_min_level_file": "ok",
        }
    )
    assert [backend.name for backend in notifier._backends] == [
        "log",
        "desktop",
        "webhook",
        "file",
    ]
    assert notifier._backends[0].min_level is NotificationLevel.WARN
    assert notifier._backends[1].min_level is NotificationLevel.ERROR
    assert notifier._backends[2].min_level is NotificationLevel.CRITICAL
    assert notifier._backends[3].min_level is NotificationLevel.INFO


@pytest.mark.asyncio
async def test_overflow_delivery_failures_and_config_helper_edges(monkeypatch):
    from huey.banana_brain.notifications import (
        _cfg_bool,
        _cfg_get,
        _cfg_str,
    )

    notifier = Notifier({"notifications_enabled": True})
    assert _cfg_get(object(), "missing") is None
    assert _cfg_str({"value": "ready"}, "value") == "ready"
    assert _cfg_bool({"value": " YES "}, "value", False) is True
    assert _cfg_bool({"value": 0}, "value", True) is False

    class ContendedQueue:
        maxsize = 1

        def put_nowait(self, _notification):
            raise asyncio.QueueFull

        def get_nowait(self):
            raise asyncio.QueueEmpty

    notifier._queue = ContendedQueue()
    await notifier.notify("info", "overflow", "message")
    assert notifier.get_stats()["dropped_overflow"] == 1

    notifier._queue = asyncio.Queue()
    note_item = note()
    notifier._queue.put_nowait(note_item)

    async def fail_delivery(_notification):
        notifier._stop_event.set()
        raise RuntimeError("backend orchestration failed")

    monkeypatch.setattr(notifier, "_deliver", fail_delivery)
    await notifier._delivery_loop()
    assert notifier._queue._unfinished_tasks == 0

    notifier._stop_event.clear()
    notifier._queue = asyncio.Queue()
    notifier._queue.put_nowait(note())

    async def cancel_delivery(_notification):
        raise asyncio.CancelledError

    monkeypatch.setattr(notifier, "_deliver", cancel_delivery)
    with pytest.raises(asyncio.CancelledError):
        await notifier._delivery_loop()
    assert notifier._queue._unfinished_tasks == 0
