#!/usr/bin/env python3
"""Export canonical Command Center seed data."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from huey.apps.command_center.static_config import export_frontend_config
from huey.gui.defaults import (
    default_migration_phases,
    default_operator_panel_state,
    default_repositories,
)
from huey.gui.models import dataclass_list_to_dicts, dataclass_to_dict
from huey.gui.safety import safety_banner
from huey.gui.theme import as_css_variables, as_json
from huey.gui.v1_runs import sample_v1_runs
from huey.gui.validation import all_validation_commands


def build_seed_payload() -> dict[str, object]:
    """Build the repository/phase/theme/safety seed payload."""

    return {
        "config": export_frontend_config(),
        "theme": as_json(),
        "theme_css": as_css_variables(),
        "safety": safety_banner(),
        "repositories": dataclass_list_to_dicts(default_repositories()),
        "phases": dataclass_list_to_dicts(default_migration_phases()),
        "validation_commands": dataclass_list_to_dicts(all_validation_commands()),
        "operator_panel": dataclass_to_dict(default_operator_panel_state()),
        "v1_runs": dataclass_list_to_dicts(sample_v1_runs()),
    }


def write_seed(path: Path) -> Path:
    """Write the seed payload to disk."""

    payload = build_seed_payload()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Export Command Center seed JSON")
    parser.add_argument(
        "--output",
        default="docs/tools/command-center-seed.json",
        help="Output path for the exported seed payload.",
    )
    args = parser.parse_args()
    path = write_seed(Path(args.output))
    print(f"Wrote Command Center seed to {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
