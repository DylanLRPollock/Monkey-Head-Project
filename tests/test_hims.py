from __future__ import annotations

from pathlib import Path

import pytest

from huey.messaging import HIMSMessage, HIMSStore, MessagePriority, MessageStatus


def test_hims_send_writes_message_and_queued_event(tmp_path: Path) -> None:
    store = HIMSStore(tmp_path / "hims")

    message = store.send(
        sender="spark.citizen.001",
        recipient="volt.citizen.002",
        channel="district.dispatch",
        subject="Ping",
        body="Confirm district bridge.",
        priority=MessagePriority.HIGH,
        tags=["test", "district"],
        metadata={"cycle": 1},
    )

    assert message.message_id.startswith("hims-")
    assert message.priority == MessagePriority.HIGH
    assert store.get_message(message.message_id) == message
    assert store.status_for(message.message_id) == MessageStatus.QUEUED
    assert len(store.events_for(message.message_id)) == 1


def test_hims_inbox_outbox_channel_and_status_flow(tmp_path: Path) -> None:
    store = HIMSStore(tmp_path / "hims")
    first = store.send(sender="huey.core", recipient="spark", body="Status.")
    second = store.send(sender="huey.core", recipient="spark", body="Follow-up.")
    third = store.send(sender="spark", recipient="huey.core", body="Acknowledged.")

    store.mark_delivered(first.message_id, actor="hims.router")
    store.mark_read(first.message_id, actor="spark")
    store.archive(second.message_id, actor="spark")

    assert store.status_for(first.message_id) == MessageStatus.READ
    assert store.status_for(second.message_id) == MessageStatus.ARCHIVED
    assert store.inbox("spark") == [first]
    assert store.inbox("spark", include_archived=True) == [first, second]
    assert store.outbox("huey.core") == [first, second]
    assert store.channel("general") == [first, second, third]


def test_hims_message_roundtrip_preserves_optional_fields() -> None:
    message = HIMSMessage(
        sender="huey.core",
        recipient="huey.command_center",
        body="Render status.",
        channel="operator.status",
        subject="Snapshot",
        priority=MessagePriority.URGENT,
        correlation_id="corr-1",
        parent_message_id="parent-1",
        tags=("operator", "status"),
        metadata={"safe": True},
    )

    restored = HIMSMessage.from_dict(message.to_dict())

    assert restored == message
    assert restored.tags == ("operator", "status")
    assert restored.priority == MessagePriority.URGENT


def test_hims_unknown_message_events_are_rejected(tmp_path: Path) -> None:
    store = HIMSStore(tmp_path / "hims")

    with pytest.raises(KeyError):
        store.mark_read("hims-missing", actor="spark")
