"""Tests for the top-level huey CLI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from huey import cli


def test_system_check_json(monkeypatch, capsys):
    called: Dict[str, Any] = {}

    def fake_system_check() -> Dict[str, bool]:
        called["done"] = True
        return {"os_supported": True, "python_supported": True}

    monkeypatch.setattr(
        "monkey_head.system_checks.system_check", fake_system_check, raising=True
    )

    exit_code = cli.main(["system-check", "--json"])
    assert exit_code == 0
    assert called["done"] is True
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload == {"os_supported": True, "python_supported": True}


def test_memory_sort_dry_run(tmp_path: Path, capsys):
    source = tmp_path / "RAW"
    source.mkdir()
    (source / "report.pdf").write_text("dummy")
    (source / "notes.txt").write_text("dummy")
    destination = tmp_path / "memory"

    exit_code = cli.main(
        [
            "memory-sort",
            "--source",
            str(source),
            "--destination",
            str(destination),
            "--dry-run",
            "--json",
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["source"] == str(source.resolve())
    assert payload["destination"] == str(destination.resolve())
    assert payload["moved"]
    assert payload["skipped"] == []


def test_init_respects_memory_path(tmp_path: Path, monkeypatch, capsys):
    memory_root = tmp_path / "custom-memory"
    monkeypatch.setenv("MEMORY_PATH", str(memory_root))

    exit_code = cli.main(["init", "--verbose"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert f"Memory initialised at {memory_root.resolve()}" in captured.out
    for required in ("RAW", "LOGS", "PDF", "JSON"):
        assert (memory_root / required).exists()


class _FakeRecord:
    def __init__(
        self,
        *,
        task_id: str,
        status: Any,
        assigned_agent: Optional[Any],
    ) -> None:
        self.task_id = task_id
        self.status = status
        self.assigned_agent = assigned_agent

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "assigned_agent": getattr(self.assigned_agent, "value", None),
        }


class _FakeScheduler:
    def __init__(self, records: Iterable[_FakeRecord]) -> None:
        self._records = list(records)

    def list_tasks(self) -> List[_FakeRecord]:
        return list(self._records)

    def health_provider(self) -> Any:
        class Snapshot:
            timestamp = 123.0
            cpu_percent = 42.0
            memory_available = 512
            memory_total = 1024
            battery_percent = None
            notes = "psutil not available"

        return Snapshot()


def test_agent_status_json(monkeypatch, capsys):
    from monkey_head.core.task_scheduler import Agent, TaskStatus

    records = [
        _FakeRecord(task_id="1", status=TaskStatus.RUNNING, assigned_agent=Agent.SPARK),
        _FakeRecord(task_id="2", status=TaskStatus.PENDING, assigned_agent=None),
    ]
    fake_scheduler = _FakeScheduler(records)

    import huey.api as huey_api

    monkeypatch.setattr(huey_api, "SCHEDULER", fake_scheduler)

    exit_code = cli.main(["agent-status", "--json", "--verbose"])
    assert exit_code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["total_tasks"] == 2
    assert payload["tasks_by_status"]["running"] == 1
    assert payload["tasks_by_agent"]["spark"] == 1
    assert payload["resource_snapshot"]["cpu_percent"] == 42.0
    assert payload["tasks"]


def test_deploy_dry_run_prints_expected_commands(tmp_path: Path, monkeypatch, capsys):
    compose_file = tmp_path / "docker-compose.yml"
    manifest_file = tmp_path / "k8s.yaml"
    compose_file.write_text("services: {}", encoding="utf-8")
    manifest_file.write_text("apiVersion: v1\nkind: Pod", encoding="utf-8")

    monkeypatch.setattr(cli.shutil, "which", lambda tool: f"/usr/bin/{tool}")

    exit_code = cli.main(
        [
            "deploy",
            "--compose-file",
            str(compose_file),
            "--manifest",
            str(manifest_file),
            "--dry-run",
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr().out.splitlines()
    assert any(line.startswith("[dry-run] docker compose -f") for line in captured)
    assert any(line.startswith("[dry-run] kubectl apply -f") for line in captured)
