# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.11.2025
# ==================================================
from pathlib import Path
import importlib.util

spec = importlib.util.spec_from_file_location(
    "auto_sort", Path(__file__).resolve().parents[1] / "auto-sort.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)  # type: ignore
sort_raw_files = module.sort_raw_files


def test_auto_sort(tmp_path: Path) -> None:
    base = tmp_path
    raw = base / "raw"
    raw.mkdir()
    mem = base / "memory"
    mem.mkdir()

    (raw / "file.txt").write_text("data")
    (raw / "img.jpg").write_text("image")
    (raw / "doc.PDF").write_text("pdf")

    sort_raw_files(base)

    assert not any(raw.iterdir())
    assert (mem / "TXT" / "file.txt").is_file()
    assert (mem / "JPEG" / "img.jpg").is_file()
    assert (mem / "PDF" / "doc.PDF").is_file()
