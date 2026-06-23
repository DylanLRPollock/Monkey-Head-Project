# Media tool consolidation

This note records the consolidation of media helpers under the canonical `huey.media` package.

## Decision

Media and FFmpeg-oriented helpers should live under:

```text
src/huey/media/
```

The `huey.audio` package may keep compatibility adapters for existing imports, but implementation should be centralized under `huey.media` when the helper is part of the shared media pipeline.

## Canonical media modules

Use these modules for media operations:

- `huey.media.media_manager`
- `huey.media.ffmpeg_validator`
- `huey.media.audio_analysis`
- `huey.media.speech_pipeline`
- `huey.media.video_pipeline`
- `huey.media.media_conversion`
- `huey.media.convert_mkv_to_mp4`
- `huey.media.convert_png_to_jpeg`
- `huey.media.convert_video_to_gif`

## Compatibility adapters

The following compatibility adapter remains intentionally:

- `huey.audio.audio_analysis`

It re-exports the canonical `huey.media.audio_analysis` public API so older imports keep working while the project transitions to the standardized media package.

## Rationale

The project previously had overlapping media helper locations across memory, audio, and root-level bridge modules. Consolidating implementation under `huey.media` makes the package layout easier to maintain and aligns FFmpeg, audio analysis, speech preparation, and video preprocessing under one domain boundary.
