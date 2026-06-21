from __future__ import annotations

from huey.connectors.pyhuey.tool_manifest import build_manifest


def test_manifest_blocks_arbitrary_shell() -> None:
    manifest = build_manifest()
    assert manifest["policy"]["blocks_arbitrary_shell"] is True
    assert any(tool["name"] == "check_ffmpeg_environment" for tool in manifest["tools"])

