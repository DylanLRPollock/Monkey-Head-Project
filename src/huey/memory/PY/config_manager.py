# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Config Manager module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.20.2026
# ==================================================
from __future__ import annotations

import configparser
import json
import os
from pathlib import Path
from typing import Any

from huey.os.utils.paths import get_memory_path

DEFAULT_CONFIG = Path("config") / "pygpt_net" / "config.json"


class ConfigManager:
    """Load and persist simple project configuration files.

    The legacy scripts still use flat JSON files, while the logging tests exercise
    INI-style configuration.  This manager supports both formats and keeps the
    public API intentionally small for compatibility.
    """

    def __init__(self, config_path: str | os.PathLike[str] | None = None) -> None:
        self.path = self._resolve_path(config_path)
        self.config_path = str(self.path)
        self._format = self._detect_format(self.path)
        self.config = self.load_config()

    @staticmethod
    def _resolve_path(
        config_path: str | os.PathLike[str] | None,
    ) -> Path:
        candidate = config_path or os.environ.get("MONKEY_HEAD_CONFIG")
        if candidate:
            return Path(candidate).expanduser().resolve()
        return (get_memory_path(create=True) / DEFAULT_CONFIG).resolve()

    @staticmethod
    def _detect_format(path: Path) -> str:
        if path.suffix.lower() in {".ini", ".cfg"}:
            return "ini"
        return "json"

    @staticmethod
    def _get_nested(config: dict[str, Any], key: str, default: Any) -> Any:
        if key in config:
            return config[key]

        current: Any = config
        for part in key.split("."):
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
        return current

    def _load_ini(self) -> dict[str, Any]:
        parser = configparser.ConfigParser()
        parser.read(self.path, encoding="utf-8")
        config: dict[str, Any] = {}
        if parser.defaults():
            config.update(dict(parser.defaults()))
        for section in parser.sections():
            config[section] = {key: value for key, value in parser.items(section)}
        return config

    def load_config(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}

        if self._format == "ini":
            return self._load_ini()

        with self.path.open("r", encoding="utf-8") as file_obj:
            try:
                data = json.load(file_obj)
            except json.JSONDecodeError:
                return {}

        return data if isinstance(data, dict) else {}

    def _save_ini(self) -> None:
        parser = configparser.ConfigParser()
        for key, value in self.config.items():
            if isinstance(value, dict):
                parser[key] = {
                    nested_key: str(nested_value)
                    for nested_key, nested_value in value.items()
                }
            else:
                parser["DEFAULT"][str(key)] = str(value)

        with self.path.open("w", encoding="utf-8") as file_obj:
            parser.write(file_obj)

    def save_config(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self._format == "ini":
            self._save_ini()
            return

        with self.path.open("w", encoding="utf-8") as file_obj:
            json.dump(self.config, file_obj, indent=4, sort_keys=True)

    def get_setting(self, key: str, default: Any = None) -> Any:
        return self._get_nested(self.config, key, default)

    def get_section(
        self, section: str, default: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        default_values = dict(default or {})
        value = self.config.get(section)
        if isinstance(value, dict):
            merged = dict(default_values)
            merged.update(value)
            return merged

        prefix = f"{section}."
        flattened = {
            key[len(prefix) :]: value
            for key, value in self.config.items()
            if isinstance(key, str) and key.startswith(prefix)
        }
        if flattened:
            merged = dict(default_values)
            merged.update(flattened)
            return merged
        return default_values

    def set_setting(self, key: str, value: Any) -> None:
        self.config[key] = value
        self.save_config()

    def update_settings(self, data: dict[str, Any]) -> None:
        """Update multiple settings at once and persist them."""

        self.config.update(data)
        self.save_config()
