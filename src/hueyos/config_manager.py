"""Unified configuration manager for the Monkey Head Project."""

from __future__ import annotations

import json
import os
from configparser import ConfigParser
from pathlib import Path
from typing import Any, Mapping

_DEFAULT_CONFIG_NAME = "main.config"


class ConfigManager:
    """Read and persist project configuration data."""

    def __init__(self, config_path: str | os.PathLike[str] | None = None) -> None:
        self.path = self._resolve_path(config_path)
        self._data: dict[str, Any] = self._load()

    def _resolve_path(self, config_path: str | os.PathLike[str] | None) -> Path:
        if config_path is not None:
            return Path(config_path)

        env_path = os.environ.get("MONKEY_HEAD_CONFIG")
        if env_path:
            return Path(env_path)

        project_root = Path(__file__).resolve().parents[2]
        return project_root / "config" / _DEFAULT_CONFIG_NAME

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            text = self.path.read_text(encoding="utf-8")
        except OSError:
            return {}

        if not text.strip():
            return {}

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            parser = ConfigParser()
            parser.read_string(text)
            data: dict[str, Any] = {
                section: dict(parser.items(section)) for section in parser.sections()
            }
            if parser.defaults():
                data.setdefault("DEFAULT", dict(parser.defaults()))
            return data

    def save_config(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(self._data, file, indent=2, sort_keys=True)

    def get_setting(self, key: str, default: Any | None = None) -> Any:
        parts = key.split(".") if key else []
        current: Any = self._data
        for part in parts:
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
        return current if parts else self._data or default

    def get_section(
        self, section: str, default: Mapping[str, Any] | None = None
    ) -> dict[str, Any]:
        value = self.get_setting(section, default)
        if isinstance(value, Mapping):
            return dict(value)
        return dict(default or {})

    def set_setting(self, key: str, value: Any) -> None:
        parts = key.split(".") if key else []
        if not parts:
            raise ValueError("key must not be empty")

        current = self._data
        for part in parts[:-1]:
            if not isinstance(current.get(part), dict):
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
        self.save_config()

    def update_settings(self, data: Mapping[str, Any]) -> None:
        def _merge(
            target: dict[str, Any], updates: Mapping[str, Any]
        ) -> dict[str, Any]:
            for key, value in updates.items():
                if (
                    key in target
                    and isinstance(target[key], dict)
                    and isinstance(value, Mapping)
                ):
                    target[key] = _merge(dict(target[key]), value)
                else:
                    target[key] = value
            return target

        self._data = _merge(dict(self._data), data)
        self.save_config()

    def as_dict(self) -> dict[str, Any]:
        return json.loads(json.dumps(self._data))


__all__ = ["ConfigManager"]
