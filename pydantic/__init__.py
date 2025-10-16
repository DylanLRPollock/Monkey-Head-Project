# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Package initializer for pydantic

"""Lightweight stand-in for the ``pydantic`` package used in the tests.

The real dependency is not available in the execution environment, but the
code exercised by the tests only requires a subset of the ``BaseModel``
behaviour and the :func:`Field` helper.  The implementation below provides just
enough functionality for the API layer to construct request/response payloads.
It is intentionally small and does not aim to be feature complete.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Tuple

__all__ = ["BaseModel", "Field"]


class _UnsetType:
    pass


_UNSET = _UnsetType()


@dataclass
class FieldInfo:
    default: Any = _UNSET
    default_factory: Callable[[], Any] | None = None
    metadata: Dict[str, Any] | None = None


def Field(
    default: Any = _UNSET,
    *,
    default_factory: Callable[[], Any] | None = None,
    **metadata: Any,
) -> FieldInfo:
    return FieldInfo(default=default, default_factory=default_factory, metadata=metadata)


class ModelMeta(type):
    def __new__(mcls, name: str, bases: Tuple[type, ...], namespace: Dict[str, Any]):
        annotations = dict(namespace.get("__annotations__", {}))
        fields: Dict[str, Tuple[Any, Any]] = {}

        for base in reversed(bases):
            if hasattr(base, "__fields__"):
                fields.update(base.__fields__)  # type: ignore[attr-defined]

        for field_name, annotation in annotations.items():
            if field_name.startswith("__"):
                continue
            default = namespace.get(field_name, _UNSET)
            if isinstance(default, FieldInfo):
                namespace.pop(field_name)
            elif default is not _UNSET:
                namespace.pop(field_name)
            fields[field_name] = (annotation, default)

        namespace["__fields__"] = fields
        cls = super().__new__(mcls, name, bases, namespace)
        return cls


class BaseModel(metaclass=ModelMeta):
    __fields__: Dict[str, Tuple[Any, Any]] = {}

    def __init__(self, **data: Any) -> None:
        values: Dict[str, Any] = {}
        for name, (annotation, default) in self.__fields__.items():
            if name in data:
                values[name] = data.pop(name)
            else:
                values[name] = self._resolve_default(name, default)
        data.clear()
        for name, value in values.items():
            setattr(self, name, value)

    @staticmethod
    def _resolve_default(name: str, default: Any) -> Any:
        if isinstance(default, FieldInfo):
            if default.default is not _UNSET:
                return default.default
            if default.default_factory is not None:
                return default.default_factory()
            raise TypeError(f"Field '{name}' requires a value")
        if default is _UNSET:
            return None
        return default

    def model_dump(self) -> Dict[str, Any]:
        return {name: _coerce(getattr(self, name)) for name in self.__fields__}

    dict = model_dump


def _coerce(value: Any) -> Any:
    from enum import Enum

    if isinstance(value, BaseModel):
        return value.model_dump()
    if isinstance(value, list):
        return [_coerce(item) for item in value]
    if isinstance(value, dict):
        return {key: _coerce(item) for key, item in value.items()}
    if isinstance(value, Enum):
        return value.value  # type: ignore[return-value]
    return value
