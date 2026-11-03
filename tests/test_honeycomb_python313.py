"""Python 3.13 Honeycomb and agent-memory integration contracts.

Exercise the real maintained storage/index/monitor implementations in an
isolated temporary directory. Nothing touches the configured live memory.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, get_type_hints

from huey.agents.memory import AgentMemory, MemoryEntry
from huey.honeycomb.index import HoneycombContentMapping, HoneycombIndex
from huey.honeycomb.monitor import HoneycombMonitor
from huey.honeycomb.storage import HoneycombStorage


def test_python313_public_annotations_are_resolvable() -> None:
    assert get_type_hints(MemoryEntry)["payload"] == dict[str, Any]
    assert get_type_hints(AgentMemory.recall)["limit"] == int | None
    assert get_type_hints(HoneycombStorage.__init__)["base_dir"] == (
        Path | str | None
    )
    assert get_type_hints(HoneycombContentMapping)["retention"] == str | None
    assert get_type_hints(HoneycombMonitor.__init__)["index"] == (
        HoneycombIndex | None
    )
    annotation = get_type_hints(HoneycombIndex.__init__)["mappings"]
    assert annotation == Mapping[str, HoneycombContentMapping] | None
    assert get_type_hints(HoneycombMonitor.usage_totals)["comb_usage"] == (
        Iterable[dict[str, object]]
    )


def test_agent_memory_isolated_by_agent_and_topic(tmp_path: Path) -> None:
    with HoneycombStorage(base_dir=tmp_path / "storage") as storage:
        alpha = AgentMemory(storage, "alpha")
        beta = AgentMemory(storage, "beta")
        first = alpha.remember("decision", {"choice": "A"})
        alpha.remember("observation", {"temperature": 21})
        beta.remember("decision", {"choice": "B"})

        recalled = alpha.recall("decision")
        assert len(recalled) == 1
        assert recalled[0].key == first.key
        assert recalled[0].payload == {"choice": "A"}
        assert alpha.last_decisions(limit=1) == recalled
        assert beta.recall("decision")[0].payload == {"choice": "B"}
        assert beta.recall("observation") == []


def test_conversation_metadata_does_not_mutate_caller(tmp_path: Path) -> None:
    with HoneycombStorage(base_dir=tmp_path / "storage") as storage:
        agent = AgentMemory(storage, "alpha")
        original = {"source": "test"}
        saved = agent.log_conversation(
            "conversation-1",
            role="user",
            content="hello",
            metadata=original,
        )

        assert original == {"source": "test"}
        assert saved.data["content"] == "hello"
        assert saved.data["metadata"]["agent_id"] == "alpha"
        assert saved.data["metadata"]["source"] == "test"
        assert len(list(storage.iter_conversation("conversation-1"))) == 1


def test_index_and_monitor_roundtrip(tmp_path: Path) -> None:
    with HoneycombStorage(base_dir=tmp_path / "storage") as storage:
        index = HoneycombIndex(storage)
        stored = index.store_payload(
            "logs",
            {"message": "hello"},
            metadata={"source": "integration-test"},
            cell_id="fixture-1",
        )
        assert stored.key == "telemetry/logs/fixture-1"

        records = index.records_for_content_type("logs")
        assert len(records) == 1
        assert records[0].payload == {"message": "hello"}
        assert records[0].metadata == {"source": "integration-test"}

        monitor = HoneycombMonitor(storage, index=index)
        report = monitor.build_usage_report()
        assert report["totals"]["cells"] == 1
        assert report["totals"]["combs"] == 1
        assert any(
            item["content_type"] == "logs" and item["cells"] == 1
            for item in report["content_types"]
        )


def test_closed_storage_rejects_new_agent_memory(tmp_path: Path) -> None:
    storage = HoneycombStorage(base_dir=tmp_path / "storage")
    agent = AgentMemory(storage, "alpha")
    storage.close()

    try:
        agent.remember("decision", {"choice": "A"})
    except RuntimeError as exc:
        assert "closed" in str(exc)
    else:
        raise AssertionError("Closed storage must reject agent writes")
