"""Coverage for serial bridge lifecycle and Honeycomb snapshot edge paths."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from huey.os.honeycomb.backup import (
    BackupError,
    perform_rsync_snapshot,
    restore_snapshot,
)
from huey.os.legacy.connectors import (
    EmulatedLegacyConnector,
    LegacyConnectorFactory,
    SerialLegacyConnector,
)


@pytest.mark.asyncio
async def test_serial_connector_lifecycle_uses_configured_transport(
    monkeypatch,
) -> None:
    events = []

    class FakeSerial:
        def __init__(self, port, baudrate, timeout):
            events.append(("open", port, baudrate, timeout))

        def write(self, payload):
            events.append(("write", payload))

        def read(self, size):
            events.append(("read", size))
            return b"reply"

        def close(self):
            events.append(("close",))

    monkeypatch.setattr(
        "huey.os.legacy.connectors.serial", SimpleNamespace(Serial=FakeSerial)
    )
    connector = SerialLegacyConnector(port="/dev/fake", baudrate=19200, timeout=0.4)
    with pytest.raises(RuntimeError, match="not been initialised"):
        await connector.send(b"x")
    with pytest.raises(RuntimeError, match="not been initialised"):
        await connector.receive()

    await connector.connect()
    await connector.send(b"hello")
    assert await connector.receive(3) == b"reply"
    await connector.close()
    await connector.close()
    assert events == [
        ("open", "/dev/fake", 19200, 0.4),
        ("write", b"hello"),
        ("read", 3),
        ("close",),
    ]
    assert connector._serial is None


def test_connector_factory_normalizes_mode_and_rejects_unknown() -> None:
    assert isinstance(
        LegacyConnectorFactory.create({"mode": "EMULATED"}), EmulatedLegacyConnector
    )
    with pytest.raises(ValueError, match="Unsupported legacy connector mode: other"):
        LegacyConnectorFactory.create({"mode": "other"})
    serial = LegacyConnectorFactory.create(
        {"mode": "serial", "port": "COM4", "baudrate": "115200", "timeout": "2.5"}
    )
    assert isinstance(serial, SerialLegacyConnector)
    assert (serial.baudrate, serial.timeout) == (115200, 2.5)


def test_emulated_connector_limits_reads_without_consuming_extra_messages() -> None:
    import asyncio

    async def scenario():
        connector = EmulatedLegacyConnector()
        await connector.inject_emulator_response(b"abcdef")
        await connector.inject_emulator_response(b"next")
        assert await connector.receive(3) == b"abc"
        assert await connector.receive() == b"next"
        await connector.close()

    asyncio.run(scenario())


def test_backup_copies_files_and_reports_metadata(tmp_path: Path) -> None:
    source_file = tmp_path / "source.bin"
    source_file.write_bytes(b"payload")
    copied = tmp_path / "copies" / "source.bin"
    result = perform_rsync_snapshot(source_file, copied)
    assert copied.read_bytes() == b"payload"
    assert result.files_copied == 1
    assert result.bytes_copied == 7
    assert result.operation == "backup"
    assert result.elapsed_seconds >= 0
    assert result.as_dict()["destination"] == str(copied.resolve())
    restored = restore_snapshot(copied, tmp_path / "restored.bin")
    assert restored.operation == "restore"
    assert restored.destination.read_bytes() == b"payload"


def test_backup_and_restore_guard_overwrites_and_missing_inputs(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    target = tmp_path / "target"
    target.mkdir()
    (target / "existing").write_text("keep", encoding="utf-8")
    with pytest.raises(BackupError, match="destination already exists"):
        perform_rsync_snapshot(source, target)
    (source / "new").write_text("new", encoding="utf-8")
    copied = perform_rsync_snapshot(source, target, overwrite=True)
    assert copied.files_copied == 1
    assert (target / "existing").read_text(encoding="utf-8") == "keep"
    assert (target / "new").read_text(encoding="utf-8") == "new"

    with pytest.raises(BackupError, match="source does not exist"):
        restore_snapshot(tmp_path / "missing", tmp_path / "restore")


def test_backup_wraps_filesystem_errors_and_empty_directory_is_valid(
    tmp_path: Path, monkeypatch
) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    result = perform_rsync_snapshot(empty, tmp_path / "empty-copy")
    assert result.files_copied == 0
    assert result.bytes_copied == 0

    def fail_copy(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr("huey.os.honeycomb.backup.shutil.copy2", fail_copy)
    full = tmp_path / "full"
    full.mkdir()
    (full / "file").write_text("data", encoding="utf-8")
    with pytest.raises(BackupError, match="disk full") as raised:
        perform_rsync_snapshot(full, tmp_path / "snapshot")
    assert isinstance(raised.value.__cause__, OSError)
