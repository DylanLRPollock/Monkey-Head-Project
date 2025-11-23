#!/usr/bin/env python3
# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Check Inter Program Connectivity module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated:   06.12.2025
# ==================================================
"""Verify that hueyos and pygpt_net modules import successfully."""

import importlib
import sys
from pathlib import Path


def check_inter_program_connectivity() -> bool:
    """Return ``True`` if required packages can be imported."""
    try:
        importlib.import_module("hueyos")
    except Exception:
        return False

    try:
        importlib.import_module("pygpt_net")
    except Exception:
        root = Path(__file__).resolve().parents[1]
        submodule = root / "repo" / "pygpt-MHP" / "src"
        if submodule.exists() and str(submodule) not in sys.path:
            sys.path.append(str(submodule))
        try:
            importlib.import_module("pygpt_net")
        except Exception:
            return False
    return True


def main() -> None:
    if check_inter_program_connectivity():
        print("Inter-program connectivity verified")
        sys.exit(0)
    print("Inter-program connectivity failed", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
