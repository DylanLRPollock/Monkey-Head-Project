import os
import time
from pathlib import Path

from huey.memory.PY.storage_management import StorageManager


def test_remove_older_than_logs_delete_failures(tmp_path, monkeypatch, caplog):
    base = tmp_path / "memory"
    base.mkdir()
    stale = base / "stale.txt"
    stale.write_text("data", encoding="utf-8")

    old_time = time.time() - 10 * 86400
    os.utime(stale, (old_time, old_time))

    original_unlink = Path.unlink

    def fail_unlink(self: Path, *args, **kwargs):
        if self.name == "stale.txt":
            raise PermissionError("blocked")
        return original_unlink(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_unlink)

    mgr = StorageManager(base)
    caplog.set_level("WARNING")

    removed = mgr.remove_older_than(7)

    assert removed == 0
    assert stale.exists()
    assert any(
        "Failed to delete old file" in rec.message and "stale.txt" in rec.message
        for rec in caplog.records
    )
