---
name: ffmpeg-audio-extract
description: recommend preservation-first ffmpeg commands for users who paste ffprobe or mediainfo metadata and want to extract one or more audio tracks from a video. use when chatgpt needs to decide whether to stream copy or convert to flac, how to map multiple tracks to separate files, how to preserve language and title metadata, and return ready-to-run linux terminal commands with warnings about lossy-to-lossy transcodes.
---

# Ffmpeg Audio Extract

## Overview

Extract audio tracks from a video with the least processing that still gives the user what they need. Stream copy is preferred when the source codec is already an acceptable target. Convert only when the user requests another format or a delivery requirement needs it.

## Workflow

1. Read the pasted metadata carefully.
2. Extract the facts that materially affect extraction:
   - number of audio streams and their indices
   - audio codecs
   - sample rate, channel layout, bit depth
   - language and title tags
   - whether any audio track is lossless
3. Classify the extraction goal:
   - **keep original codec** when the user accepts the source codec
   - **lossless archive** when the user wants a FLAC or WAV master
   - **uncertain** when the goal is not stated
4. Choose one recommendation path:
   - **stream copy extraction** for keeping the original codec
   - **FLAC extraction** for lossless archival
5. Return a concise assessment, one recommended command, a short explanation, and warnings.

## Command-building rules

### 1) Extract one track by stream index

```bash
ffmpeg -i "input.ext" -map 0:a:0 -vn -sn -c:a copy "track-0.mka"
```

Use `-map 0:a:N` for the Nth audio stream (zero-based among audio streams). Choose an output container/extension supported by the source codec. `.mka` is a flexible Matroska audio container; do not give a copied codec a misleading extension.

### 2) Convert to FLAC only when requested or justified

```bash
ffmpeg -i "input.ext" -map 0:a:0 -vn -sn -c:a flac "track-0.flac"
```

FLAC preserves decoded samples from a lossless source. For lossy source audio it does not restore lost information and usually makes a larger file. Do not convert to FLAC merely because a source codec is unknown; inspect it first.

### 3) Multiple tracks

Create one output per requested track, or use a multi-track container if the user wants them together. Preserve known language/title tags and tell the user which source stream each output represents. Preserve sample rate and channel layout unless the user requests a change.

## Output format

Use exactly these labels in this order:

### Source assessment
- Summarize the audio streams in 3 to 6 short bullets.
- State which stream indices exist and what codecs they use.
- State whether any track is already lossless.

### Recommended command
- Return one ready-to-run FFmpeg command in a fenced bash block.
- For multiple tracks, return one fenced block containing each command on its own line.

### Why this command
- Explain the reasoning in 2 to 5 bullets.
- Mention stream mapping, copy versus convert, container choice, and metadata handling.

### Warnings
- Always warn that converting lossy audio to FLAC does not restore lost quality.
- Warn that re-encoding a lossy codec to another lossy codec loses additional quality.
- Warn that channel layout and sample rate are preserved unless explicitly changed.
- Warn to verify the extracted audio stream with ffprobe.

## Decision defaults

When uncertain, prefer the safer path:

- stream copy when the codec is acceptable
- convert only to the requested or required format; FLAC is not a default for lossy sources
- preserve sample rate and channel layout
- extract one track per file
- mka or flac as output

## Practical command patterns

### List audio streams

```bash
ffprobe -v error -select_streams a -show_entries stream=index,codec_name,sample_rate,channels:stream_tags=language,title \
  -of default=nw=1 input.ext
```
