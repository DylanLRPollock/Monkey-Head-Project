"""Cover human-readable CLI summaries and validation exits."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

from huey.memory.PY import cli


class _Shadow:
    def __init__(self, root):
        self.root = Path(root)

    def summary(self):
        return {
            "shadow_root": str(self.root),
            "ledger_path": str(self.root / "ledger.jsonl"),
            "messages_total": 4,
            "ledger_entries_total": 7,
            "lineages_total": 1,
            "mailboxes": {"archived": 2, "executed": 2},
        }

    def list_mailbox(self, mailbox):
        return (
            [
                {
                    "message_id": "message-1",
                    "intent_type": "request",
                    "status": "executed",
                    "lineage_metadata": {"root_lineage_id": "root-1"},
                }
            ]
            if mailbox == "executed"
            else []
        )

    def lineage(self, lineage_id):
        if lineage_id == "missing":
            raise FileNotFoundError("HIMS lineage not found: missing")
        return {
            "shadow_root": str(self.root),
            "root_lineage_id": lineage_id,
            "message_count": 1,
            "ledger_entries_total": 2,
            "messages": [
                {
                    "message_id": "message-1",
                    "intent_type": "request",
                    "status": "executed",
                    "current_mailbox": "executed",
                }
            ],
        }


def test_hims_human_summaries_and_mailbox(monkeypatch, capsys, tmp_path):
    import huey.hims.shadow

    monkeypatch.setattr(huey.hims.shadow, "ShadowHIMS", _Shadow)
    root = tmp_path / "shadow"
    root.mkdir()
    assert (
        cli._cmd_hims_summary(argparse.Namespace(shadow_root=str(root), json=False))
        == 0
    )
    summary = capsys.readouterr().out
    assert "Messages: 4" in summary
    assert "  archived: 2" in summary

    assert (
        cli._cmd_hims_mailbox(
            argparse.Namespace(shadow_root=str(root), mailbox="executed", json=False)
        )
        == 0
    )
    mailbox = capsys.readouterr().out
    assert "Mailbox: executed" in mailbox
    assert "message-1 request executed lineage=root-1" in mailbox


def test_hims_lineage_display_and_missing_lineage(monkeypatch, capsys, tmp_path):
    import huey.hims.shadow

    monkeypatch.setattr(huey.hims.shadow, "ShadowHIMS", _Shadow)
    root = tmp_path / "shadow"
    root.mkdir()
    assert (
        cli._cmd_hims_lineage(
            argparse.Namespace(shadow_root=str(root), lineage_id="root-1", json=False)
        )
        == 0
    )
    output = capsys.readouterr().out
    assert "Lineage: root-1" in output
    assert "message-1 request executed mailbox=executed" in output
    with pytest.raises(RuntimeError, match="HIMS lineage not found"):
        cli._cmd_hims_lineage(
            argparse.Namespace(shadow_root=str(root), lineage_id="missing", json=True)
        )


def test_agent_status_human_output_covers_optional_metrics(monkeypatch, capsys):
    from huey.os.core.task_scheduler import Agent, TaskStatus

    record = SimpleNamespace(
        status=TaskStatus.RUNNING,
        assigned_agent=Agent.SPARK,
        to_dict=lambda: {"task_id": "task-1"},
    )
    snapshot = SimpleNamespace(
        timestamp=1.0,
        cpu_percent=35.5,
        memory_available=750,
        memory_total=1000,
        battery_percent=80,
        notes="test snapshot",
    )
    scheduler = SimpleNamespace(
        list_tasks=lambda: [record], health_provider=lambda: snapshot
    )
    api_module = ModuleType("huey.api")
    api_module.SCHEDULER = scheduler
    monkeypatch.setitem(sys.modules, "huey.api", api_module)
    assert cli._cmd_agent_status(argparse.Namespace(json=False, verbose=True)) == 0
    output = capsys.readouterr().out
    assert "Total tasks: 1" in output
    assert "memory_free: 75.0%" in output
    assert "notes: test snapshot" in output


def test_v1_commands_require_mock_and_validate_inputs(tmp_path):
    with pytest.raises(RuntimeError, match="disabled by default"):
        cli._cmd_v1_run(argparse.Namespace(mock=False, audio_file="unused"))
    with pytest.raises(RuntimeError, match="Audio fixture not found"):
        cli._cmd_v1_run(
            argparse.Namespace(
                mock=True, audio_file=str(tmp_path / "missing"), log_dir=None
            )
        )
    with pytest.raises(RuntimeError, match="disabled by default"):
        cli._cmd_v1_run_queue(argparse.Namespace(mock=False, queue_dir="unused"))
    with pytest.raises(RuntimeError, match="Queue directory not found"):
        cli._cmd_v1_run_queue(
            argparse.Namespace(
                mock=True,
                queue_dir=str(tmp_path / "missing"),
                log_dir=str(tmp_path / "logs"),
            )
        )
