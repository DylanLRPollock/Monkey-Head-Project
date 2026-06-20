"""Message bus used by the speculative multi-agent runtime."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class AgentMessage:
    source: str
    target: str
    topic: str
    content: str
    metadata: dict[str, object] = field(default_factory=dict)


class AgentMessageBus:
    """Store and fan out agent messages by target identity."""

    def __init__(self) -> None:
        self._messages: list[AgentMessage] = []

    def publish(
        self,
        source: str,
        target: str,
        topic: str,
        content: str,
        *,
        metadata: dict[str, object] | None = None,
    ) -> AgentMessage:
        message = AgentMessage(
            source=source,
            target=target,
            topic=topic,
            content=content,
            metadata=dict(metadata or {}),
        )
        self._messages.append(message)
        return message

    def inbox(self, target: str) -> list[AgentMessage]:
        return [message for message in self._messages if message.target == target]

    def history(self) -> list[dict[str, object]]:
        return [
            {
                "source": message.source,
                "target": message.target,
                "topic": message.topic,
                "content": message.content,
                "metadata": dict(message.metadata),
            }
            for message in self._messages
        ]


__all__ = ["AgentMessage", "AgentMessageBus"]
