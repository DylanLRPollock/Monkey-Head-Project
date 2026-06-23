"""GPIO pin state management."""

from __future__ import annotations


class GPIOController:
    """Maintain logical GPIO pin states."""

    def __init__(self) -> None:
        self._pins: dict[int, bool] = {}

    def write(self, pin: int, value: bool) -> bool:
        self._pins[pin] = bool(value)
        return self._pins[pin]

    def read(self, pin: int) -> bool:
        return self._pins.get(pin, False)

    def snapshot(self) -> dict[int, bool]:
        return dict(self._pins)


__all__ = ["GPIOController"]
