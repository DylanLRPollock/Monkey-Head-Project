# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Function Registry module (tests)

"""Tests for the lightweight function registry utilities."""

from __future__ import annotations

import pytest

from huey.os import function_registry


@pytest.fixture(autouse=True)
def reset_registry(monkeypatch):
    """Ensure each test runs with an isolated registry."""

    monkeypatch.setattr(function_registry, "_FUNCTIONS", {})


def test_register_function_decorator_registers_callable():
    @function_registry.register_function
    def demo():
        return "demo"

    assert "demo" in function_registry.list_functions()
    assert function_registry.get_functions()["demo"]() == "demo"


def test_register_function_overwrites_existing_entry():
    @function_registry.register_function
    def sample():
        return "first"

    @function_registry.register_function
    def sample():  # noqa: F811
        return "second"

    registry = function_registry.get_functions()
    assert registry["sample"]() == "second"


def test_list_functions_returns_sorted_names():
    function_registry.register_function(lambda: None)

    @function_registry.register_function
    def alpha():
        return "alpha"

    @function_registry.register_function
    def beta():
        return "beta"

    assert function_registry.list_functions() == ["<lambda>", "alpha", "beta"]


def test_get_functions_returns_copy():
    function_registry.register_function(lambda: "original")
    copy = function_registry.get_functions()
    copy.clear()

    # The internal registry should remain intact even after mutating the copy.
    assert function_registry.list_functions() == ["<lambda>"]


def test_ensure_registered_functions_discovers_project_functions():
    registry = function_registry.ensure_registered_functions()

    assert {
        "auto_sort_memory",
        "find_pdf",
        "format_text",
        "list_available_pdfs",
    } <= set(registry)


def test_describe_and_invoke_registered_functions():
    descriptions = {
        item["name"]: item for item in function_registry.describe_functions()
    }
    result = function_registry.invoke_function(
        "format_text", text="alpha beta", line_length=20
    )

    assert descriptions["format_text"]["required_parameters"] == ["text"]
    assert descriptions["find_pdf"]["required_parameters"] == ["filename"]
    assert result == "alpha beta"
