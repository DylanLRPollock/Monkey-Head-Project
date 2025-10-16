# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Preload Data module (huey/memory/PY)

import csv
from pathlib import Path
from typing import Dict, List


BASE_DIR = Path(__file__).resolve().parents[2]


def load_prompts() -> List[Dict[str, str]]:
    """Load prompts from the CSV dataset."""
    prompts_file = BASE_DIR / "prompts" / "pygpt_prompts.csv"
    if not prompts_file.is_file():
        return []
    with prompts_file.open(encoding="utf-8") as f:
        lines = [line for line in f if line.strip()]
    reader = csv.DictReader(lines[1:])  # skip comment line
    return list(reader)


def load_memory() -> Dict[str, List[str]]:
    """Collect memory files from bundled memory directory."""
    memory_dir = BASE_DIR / "memory"
    result: Dict[str, List[str]] = {}
    if not memory_dir.is_dir():
        return result
    for sub in memory_dir.iterdir():
        if sub.is_dir():
            result[sub.name] = [str(p.resolve()) for p in sub.iterdir() if p.is_file()]
    return result


def preload_all() -> Dict[str, object]:
    """Load prompts and memory files."""
    return {
        "prompts": load_prompts(),
        "memory": load_memory(),
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Preload memory and prompts")
    parser.add_argument("--summary", action="store_true", help="Print summary only")
    args = parser.parse_args()

    data = preload_all()
    if args.summary:
        print(f"Prompts loaded: {len(data['prompts'])}")
        for key, files in data["memory"].items():
            print(f"{key}: {len(files)} files")
    else:
        print(data)


if __name__ == "__main__":
    main()
