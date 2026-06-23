from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from huey.media.media_manifest import MediaArtifact, MediaManifest, read_manifest


class MediaManifestTests(unittest.TestCase):
    def test_manifest_write_refuses_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "manifest.json"
            manifest = MediaManifest(
                source_path="fixture.mp3",
                operation="test",
                artifacts=[
                    MediaArtifact(
                        kind="audio", path="out.wav", role="transcription_wav"
                    )
                ],
            )

            manifest.write_json(output)

            with self.assertRaises(FileExistsError):
                manifest.write_json(output)

    def test_manifest_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "manifest.json"
            MediaManifest(source_path="fixture.mp3", operation="test").write_json(
                output
            )

            loaded = read_manifest(output)

            self.assertEqual(loaded["source_path"], "fixture.mp3")
            self.assertEqual(loaded["operation"], "test")


if __name__ == "__main__":
    unittest.main()
