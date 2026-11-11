"""Direct behavior coverage for small data, UI, and scheduling surfaces."""

from __future__ import annotations

from huey.data.extractor import extract_key_values, extract_sections
from huey.data.text_parser import normalize_text, split_sentences, token_frequency
from huey.gencore.scheduler import TaskScheduler
from huey.ui.adaptive_ui import AdaptiveUIEngine
from huey.ui.cli import build_cli_parser
from huey.ui.dashboard import build_dashboard
from huey.ui.interface import InterfaceController
from huey.ui.terminal import render_status_table
from huey.ui.web_ui import WebInterface


def test_text_parsing_and_extraction_handles_blanks_and_delimiters() -> None:
    assert normalize_text("  lots\n of   space ") == "lots of space"
    assert split_sentences(" \n ") == []
    assert split_sentences("First. Second! third?") == ["First.", "Second!", "third?"]
    assert token_frequency("Hi hi, Huey's v1") == {"hi": 2, "huey's": 1, "v1": 1}
    assert extract_key_values("no delimiter\n: empty key\n Name : Ada: Lovelace \nName: Grace") == {
        "Name": "Grace"
    }
    sections = extract_sections("\n\n".join(["", "Title\nFirst sentence. Second sentence!", "  "]))
    assert len(sections) == 1
    assert sections[0]["title"] == "Title"
    assert sections[0]["sentences"] == ["Title First sentence.", "Second sentence!"]


def test_ui_control_surface_selects_profiles_and_renders_views() -> None:
    engine = AdaptiveUIEngine()
    assert engine.choose(mode="diagnostics", operator="Dylan").emphasis == "telemetry"
    assert engine.choose(mode="control").density == "balanced"
    assert engine.choose(mode="anything").emphasis == "summary"

    status = {"kernel": "ok"}
    cards = build_dashboard(status)
    assert cards
    assert next(card for card in cards if card["section"] == "kernel")["value"] == "ok"
    assert render_status_table({"kernel": "ok"}).endswith("kernel | ok")
    presentation = InterfaceController().present(status, mode="control")
    assert presentation["profile"].emphasis == "actions"
    assert presentation["dashboard"] == cards
    web = WebInterface().render(status)
    assert web["routes"]["/health"] == "health summary"
    assert web["presentation"]["terminal"].startswith("section | value")


def test_ui_cli_parser_accepts_supported_modes_and_formats() -> None:
    parser = build_cli_parser()
    args = parser.parse_args(["--mode", "diagnostics", "--format", "json"])
    assert (args.mode, args.format) == ("diagnostics", "json")
    defaults = parser.parse_args([])
    assert (defaults.mode, defaults.format) == ("summary", "table")


def test_priority_scheduler_orders_tasks_and_honors_run_limit() -> None:
    scheduler = TaskScheduler()
    low_payload = {"value": 4}
    low = scheduler.schedule("low", priority=10, payload=low_payload)
    low_payload["value"] = 8
    high = scheduler.schedule("high", priority=1, handler=lambda payload: payload["value"], payload={"value": 3})
    same_priority = scheduler.schedule("same", priority=1)
    assert [task.name for task in scheduler.pending()] == ["high", "same", "low"]
    assert scheduler.run_next() is high
    assert high.result == 3 and high.status == "completed"
    assert high.as_dict()["payload"] == {"value": 3}
    first = scheduler.run_all(limit=1)
    assert first == [same_priority]
    assert len(scheduler.pending()) == 1
    last = scheduler.run_all()
    assert last == [low]
    assert low.as_dict()["payload"] == {"value": 4}
    assert scheduler.run_next() is None
    assert scheduler.run_all() == []
