"""Coverage tests for the auto-sort command-line wrapper."""

from __future__ import annotations

import json
from unittest.mock import Mock

from huey.scripts import auto_sort as cli


def test_main_json_output_forwards_all_cli_options(monkeypatch, capsys) -> None:
    summary = {
        "source": "/memory/RAW",
        "destination": "/memory",
        "moved": ["notes.txt"],
        "skipped": [],
    }
    sorter = Mock(return_value=summary)
    monkeypatch.setattr(cli, "auto_sort_memory", sorter)

    result = cli.main(
        [
            "--source",
            "/input",
            "--destination",
            "/output",
            "--dry-run",
            "--json",
        ]
    )

    assert result is summary
    sorter.assert_called_once_with(
        source_dir="/input",
        destination_root="/output",
        dry_run=True,
    )
    assert capsys.readouterr().out == json.dumps(summary, indent=2) + "\n"


def test_main_human_output_lists_moved_and_skipped_files(monkeypatch, capsys) -> None:
    summary = {
        "source": "/memory/RAW",
        "destination": "/memory",
        "moved": ["PDF/report.pdf"],
        "skipped": [".hidden"],
    }
    sorter = Mock(return_value=summary)
    monkeypatch.setattr(cli, "auto_sort_memory", sorter)

    result = cli.main([])

    assert result is summary
    sorter.assert_called_once_with(
        source_dir=None, destination_root=None, dry_run=False
    )
    assert capsys.readouterr().out == (
        "Source: /memory/RAW\n"
        "Destination: /memory\n"
        "Moved 1 file(s)\n"
        "  - PDF/report.pdf\n"
        "Skipped 1 file(s) due to naming conflicts:\n"
        "  - .hidden\n"
    )


def test_main_human_output_handles_empty_summary_lists(monkeypatch, capsys) -> None:
    summary = {
        "source": "/memory/RAW",
        "destination": "/memory",
        "moved": [],
        "skipped": [],
    }
    sorter = Mock(return_value=summary)
    monkeypatch.setattr(cli, "auto_sort_memory", sorter)

    cli.main([])

    expected = "Source: /memory/RAW\nDestination: /memory\nMoved 0 file(s)\n"
    assert capsys.readouterr().out == expected
