"""Legacy hardware support for classic systems and buses."""

from __future__ import annotations


class LegacyHardwareBridge:
    """Expose classic hardware profiles used by the project canon."""

    def profiles(self) -> list[dict[str, str]]:
        return [
            {"system": "VIC-20", "bus": "IEC"},
            {"system": "C64", "bus": "user-port"},
            {"system": "C128", "bus": "serial"},
        ]


__all__ = ["LegacyHardwareBridge"]
