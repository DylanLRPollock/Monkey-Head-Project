# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Cli module (tests)

"""Tests for the top-level huey CLI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from huey import cli
from huey.memory.PY import cli as legacy_cli


def test_system_check_json(monkeypatch, capsys):
    called: Dict[str, Any] = {}

    def fake_system_check() -> Dict[str, bool]:
        called["done"] = True
        return {"os_supported": True, "python_supported": True}

    monkeypatch.setattr(
        "hueyos.system_checks.system_check", fake_system_check, raising=True
    )

    exit_code = cli.main(["system-check", "--json"])
    assert exit_code == 0
    assert called["done"] is True
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload == {"os_supported": True, "python_supported": True}


def test_direct_legacy_cli_module_invocation_system_check(monkeypatch, capsys):
    def fake_system_check() -> Dict[str, bool]:
        return {"os_supported": True, "python_supported": True}

    monkeypatch.setattr(
        "hueyos.system_checks.system_check", fake_system_check, raising=True
    )

    exit_code = legacy_cli.main(["system-check", "--json"])
    assert exit_code == 0
    assert json.loads(capsys.readouterr().out) == {
        "os_supported": True,
        "python_supported": True,
    }


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
    from hueyos.core.task_scheduler import Agent, TaskStatus

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


def test_v1_run_mock_writes_structured_log(tmp_path: Path, capsys):
    fixture = tmp_path / "fixture.mp3"
    fixture.write_bytes(b"fake-mp3")
    log_dir = tmp_path / "logs"

    exit_code = cli.main(["v1-run", str(fixture), "--mock", "--log-dir", str(log_dir)])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    log_file = Path(output["log_file"])
    assert log_file.exists()
    lines = log_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1

    record = json.loads(lines[0])
    required = {
        "run_id",
        "timestamp_start",
        "timestamp_end",
        "source_file",
        "transcription_engine",
        "transcription_model",
        "transcript",
        "cognition_provider",
        "cognition_model",
        "response",
        "runtime_seconds",
        "exit_status",
        "error_message_if_any",
    }
    assert required.issubset(record.keys())
    assert record["source_file"] == str(fixture.resolve())
    assert record["exit_status"] == "success"


def test_v1_run_queue_mock_processes_sorted_and_handles_failures(tmp_path: Path, capsys):
    queue_dir = tmp_path / "queue"
    queue_dir.mkdir()
    log_dir = tmp_path / "logs"

    (queue_dir / "b-fixture.mp3").write_bytes(b"b")
    (queue_dir / "a-fixture.mp3").write_bytes(b"a")
    (queue_dir / "fail-fixture.mp3").write_bytes(b"f")
    (queue_dir / "skip.partial").write_bytes(b"x")
    (queue_dir / "skip.tmp").write_bytes(b"x")

    exit_code = cli.main(
        [
            "v1-run-queue",
            "--mock",
            "--queue-dir",
            str(queue_dir),
            "--log-dir",
            str(log_dir),
        ]
    )

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["total"] == 3
    assert output["processed"] == 2
    assert output["failed"] == 1

    processed_dir = queue_dir / "processed"
    assert (processed_dir / "a-fixture.mp3").exists()
    assert (processed_dir / "b-fixture.mp3").exists()
    assert (queue_dir / "fail-fixture.mp3").exists()
    assert (queue_dir / "skip.partial").exists()
    assert (queue_dir / "skip.tmp").exists()

    log_files = sorted(log_dir.glob("*.json"))
    assert [path.name for path in log_files] == [
        "a-fixture.mp3.json",
        "b-fixture.mp3.json",
        "fail-fixture.mp3.json",
    ]

    run_records = [json.loads(path.read_text(encoding="utf-8")) for path in log_files]
    assert [Path(record["source_file"]).name for record in run_records] == [
        "a-fixture.mp3",
        "b-fixture.mp3",
        "fail-fixture.mp3",
    ]
    assert run_records[0]["exit_status"] == "success"
    assert run_records[1]["exit_status"] == "success"
    assert run_records[2]["exit_status"] == "error"
    assert run_records[2]["error_message_if_any"] == "mock fixture failure"
