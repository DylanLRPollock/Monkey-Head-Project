"""Dedicated V1 proof-loop helpers."""

from huey.v1.fixture_registry import list_fixtures, load_fixture, register_fixture
from huey.v1.proof_loop import (
    generate_report,
    run_all_fixtures,
    run_fixture,
    validate_result,
)
from huey.v1.report_generator import (
    generate_html_report,
    generate_json_report,
    generate_markdown_report,
)

__all__ = [
    "generate_html_report",
    "generate_json_report",
    "generate_markdown_report",
    "generate_report",
    "list_fixtures",
    "load_fixture",
    "register_fixture",
    "run_all_fixtures",
    "run_fixture",
    "validate_result",
]
