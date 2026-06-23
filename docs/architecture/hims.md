# HIMS: Huey Internal Messaging System

HIMS is the local-first internal messaging layer for Huey subsystems, agents, districts, and operator-facing tools.

## Purpose

HIMS gives Huey a structured way to exchange internal messages without granting one subsystem direct access to another subsystem's memory. The first implementation is intentionally small, inspectable, and append-only.

## Initial implementation

The first HIMS foundation lives under:

```text
src/huey/messaging/
```

It provides:

- `HIMSMessage`: immutable message envelope
- `HIMSEvent`: append-only lifecycle event
- `HIMSStore`: JSONL-backed local message store
- `MessagePriority`: `low`, `normal`, `high`, `urgent`
- `MessageStatus`: `queued`, `delivered`, `read`, `archived`

## Storage model

By default, HIMS stores local journals under:

```text
.huey/hims/
  messages.jsonl
  events.jsonl
```

The storage root can be overridden with:

```text
HUEY_HIMS_ROOT
```

Messages are never edited in place. State changes such as delivery, read, and archive events are appended to `events.jsonl`. This keeps HIMS replayable and auditable.

## Design boundaries

HIMS is not yet a network protocol, queue daemon, or database service. It is a package-level foundation for:

- agent-to-agent communication
- district dispatch
- command-center notifications
- task handoff records
- future governance/audit messaging

## Safety rules

- No direct memory sharing between agents or districts.
- No hidden mutation of prior messages.
- No shell execution or external side effects in the core store.
- All writes are append-only JSON Lines records.
- Runtime tools should build on this package rather than inventing separate message formats.

## Example

```python
from huey.messaging import HIMSStore, MessagePriority

store = HIMSStore()
message = store.send(
    sender="huey.core",
    recipient="spark.citizen.001",
    channel="district.dispatch",
    subject="Status request",
    body="Report current readiness.",
    priority=MessagePriority.HIGH,
)

store.mark_delivered(message.message_id, actor="hims.router")
store.mark_read(message.message_id, actor="spark.citizen.001")
```

## Future phases

1. Add CLI wrappers under `scripts/hims/`.
2. Add Command Center read-only inbox views.
3. Add task/event bridge integration.
4. Add signed message receipts for higher-trust governance flows.
5. Add district-level routing policy without direct memory access.
