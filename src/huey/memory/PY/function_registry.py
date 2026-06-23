# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Function Registry module (huey)

"""Simple function registry used by high level utilities."""

from __future__ import annotations

import importlib
import inspect
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Dict, Iterable, List

_FUNCTIONS: Dict[str, Callable] = {}
_REGISTRY_MARKER = "__huey_custom_function__"
_PROJECT_MODULE_ROOT = Path(__file__).resolve().parents[2]

__all__ = [
    "describe_functions",
    "discover_function_modules",
    "ensure_registered_functions",
    "get_functions",
    "invoke_function",
    "list_functions",
    "register_function",
]


def register_function(func: Callable) -> Callable:
    """Register ``func`` in the global registry."""

    setattr(func, _REGISTRY_MARKER, True)
    _FUNCTIONS[func.__name__] = func
    return func


def _module_name_from_path(path: Path) -> str:
    relative = path.relative_to(_PROJECT_MODULE_ROOT).with_suffix("")
    parts = relative.parts[:-1] if relative.name == "__init__" else relative.parts
    return ".".join(("huey", *parts))


def discover_function_modules(
    extra_modules: Iterable[str] | None = None,
) -> List[str]:
    """Discover project modules that define registered custom functions."""

    modules: List[str] = []
    for module_path in sorted(_PROJECT_MODULE_ROOT.rglob("*.py")):
        if module_path.name == "function_registry.py" or module_path.name.startswith(
            "test_"
        ):
            continue
        source = module_path.read_text(encoding="utf-8")
        if "register_function" not in source:
            continue
        modules.append(_module_name_from_path(module_path))

    if extra_modules is not None:
        modules.extend(module for module in extra_modules if module.strip())

    ordered: List[str] = []
    seen: set[str] = set()
    for module_name in modules:
        if module_name in seen:
            continue
        seen.add(module_name)
        ordered.append(module_name)
    return ordered


def _register_tagged_functions(module: ModuleType) -> None:
    for value in vars(module).values():
        if not callable(value):
            continue
        if not getattr(value, _REGISTRY_MARKER, False):
            continue
        if getattr(value, "__module__", None) != module.__name__:
            continue
        _FUNCTIONS[value.__name__] = value


def ensure_registered_functions(
    extra_modules: Iterable[str] | None = None,
) -> Dict[str, Callable]:
    """Import and register the project's custom functions."""

    for module_name in discover_function_modules(extra_modules):
        module = importlib.import_module(module_name)
        _register_tagged_functions(module)
    return get_functions()


def list_functions() -> List[str]:
    """Return a sorted list of registered function names."""

    return sorted(_FUNCTIONS)


def get_functions() -> Dict[str, Callable]:
    """Return a copy of the registered functions."""

    return dict(_FUNCTIONS)


def describe_functions(
    extra_modules: Iterable[str] | None = None,
) -> List[Dict[str, object]]:
    """Return structured metadata for registered custom functions."""

    descriptions: List[Dict[str, object]] = []
    for name, func in sorted(ensure_registered_functions(extra_modules).items()):
        signature = inspect.signature(func)
        required_parameters = [
            parameter.name
            for parameter in signature.parameters.values()
            if parameter.default is inspect.Signature.empty
            and parameter.kind
            not in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            )
        ]
        descriptions.append(
            {
                "name": name,
                "module": getattr(func, "__module__", ""),
                "signature": str(signature),
                "doc": inspect.getdoc(func) or "",
                "required_parameters": required_parameters,
            }
        )
    return descriptions


def invoke_function(name: str, /, *args: Any, **kwargs: Any) -> Any:
    """Invoke a registered custom function by name."""

    functions = ensure_registered_functions()
    try:
        func = functions[name]
    except KeyError as exc:
        raise KeyError(f"Unknown registered function: {name}") from exc

    inspect.signature(func).bind(*args, **kwargs)
    return func(*args, **kwargs)
