from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def load_generator():
    path = Path(__file__).resolve().parents[1] / "scripts" / "repo" / "build_wiki.py"
    spec = importlib.util.spec_from_file_location("build_wiki", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_complete_wiki_build(tmp_path: Path) -> None:
    wiki = load_generator()
    manifest = wiki.build(tmp_path)
    assert manifest["current_pages"] >= 66
    assert manifest["compatibility_pages"] >= 12
    assert (tmp_path / "Home.md").is_file()
    assert (tmp_path / "Architecture.md").is_file()
    assert (tmp_path / "HueyNexusController.md").is_file()
    assert (tmp_path / "Page-Index.md").is_file()
    assert (tmp_path / "_Sidebar.md").is_file()
    assert (tmp_path / "_Footer.md").is_file()
    assert (tmp_path / "wiki-manifest.json").is_file()
    assert (tmp_path / "SHA256SUMS").is_file()


def test_manifest_matches_generated_pages(tmp_path: Path) -> None:
    wiki = load_generator()
    wiki.build(tmp_path)
    manifest = json.loads((tmp_path / "wiki-manifest.json").read_text())
    markdown = sorted(p.name for p in tmp_path.glob("*.md"))
    listed = sorted(item["file"] for item in manifest["files"])
    assert markdown == listed
    assert all(len(item["sha256"]) == 64 for item in manifest["files"])


def test_every_current_page_has_status_and_sources(tmp_path: Path) -> None:
    wiki = load_generator()
    manifest = wiki.build(tmp_path)
    compatibility = manifest["compatibility_pages"]
    current = 0
    for page in tmp_path.glob("*.md"):
        if page.name.startswith("_"):
            continue
        text = page.read_text()
        if "Historical or compatibility page" in text:
            continue
        current += 1
        assert wiki.DATE in text
        assert "## Repository sources" in text
    assert current == manifest["current_pages"]
    assert compatibility >= 12


def test_legacy_targets_resolve(tmp_path: Path) -> None:
    wiki = load_generator()
    nav, _ = wiki.load_data()
    wiki.build(tmp_path)
    names = {p.stem for p in tmp_path.glob("*.md")}
    for old, info in nav["legacy_pages"].items():
        assert old in names
        assert info["target"] in names
