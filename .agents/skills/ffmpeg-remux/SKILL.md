---
name: ffmpeg-remux
description: recommend preservation-first ffmpeg commands for users who paste ffprobe or mediainfo metadata and want to change container without re-encoding, for example mp4 to mkv or ts to mp4. use when chatgpt needs to check codec and container compatibility, choose stream mappings, handle unsupported subtitles or data streams, and return ready-to-run linux terminal commands with warnings about silent stream loss and playback incompatibility.
---

# Ffmpeg Remux

## Overview

Change the container while leaving every stream bit-identical. Remuxing is the cheapest and safest transformation available, but it fails or silently drops streams when the target container cannot hold them.

## Workflow

1. Read the pasted metadata carefully.
2. Extract the facts that determine container compatibility:
   - source container
   - video codec
   - audio codecs and channel layouts
   - subtitle codecs
   - attached pictures, chapters, and data streams
   - color metadata
   - faststart requirements when relevant
3. Classify each stream as:
   - **supported** by the target container
   - **unsupported** by the target container
   - **uncertain** when the codec profile or tag is unclear
4. Choose one recommendation path:
   - **direct remux** when every kept stream is supported
   - **selective remux** when some streams must be dropped or converted
5. Return a concise assessment, one recommended command, a short explanation, and warnings.

## Command-building rules

### 1) Direct remux

```bash
ffmpeg -i "input.ext" -map 0 -c copy -map_metadata 0 -map_chapters 0 "output.mkv"
```

Use `-map 0` only when every stream can be represented in the output container. `-c copy` avoids decoding and re-encoding media payloads; it does not guarantee every muxer will preserve every type of metadata or side data.

### 2) Selective remux

```bash
ffmpeg -i "input.ext" \
  -map 0:v:0 -map '0:a?' -map '0:s?' \
  -c copy -map_metadata 0 -map_chapters 0 "output.mkv"
```

Map data, attachments, and additional tracks explicitly when they matter. If a stream is omitted, tell the user. Do not convert a codec and call the result a remux.

### 3) Container compatibility

Check compatibility for every mapped codec and the target players. MKV is broadly compatible with many codecs, but not every player supports every valid stream. MP4, WebM, and MPEG-TS each have narrower codec and metadata support; verify the precise target rather than relying on a blanket list. Add `-movflags +faststart` only for MP4 when progressive download is desired.

### 4) Verify

Preserve metadata and chapters when supported, then inspect the output streams and playback. A remux changes the container, not media quality.

## Output format

Use exactly these labels in this order:

### Source assessment
- Summarize the source in 3 to 6 short bullets.
- State which streams are supported, unsupported, or uncertain for the target container.
- State whether direct remux is safe.

### Recommended command
- Return one ready-to-run FFmpeg command in a fenced bash block.
- Use descriptive placeholder filenames if the real path is not provided.

### Why this command
- Explain the reasoning in 2 to 5 bullets.
- Mention stream mapping, container choice, metadata preservation, and why no re-encode is used.

### Warnings
- Always warn that remux does not improve quality.
- Warn when any stream is dropped or unsupported.
- Warn that some players reject valid MKV or MP4 files with unusual codecs.
- Warn to verify the output stream list with ffprobe.

## Decision defaults

When uncertain, prefer the safer path:

- choose mkv as the target
- keep all supported streams
- preserve metadata and chapters
- never silently re-encode
- verify with ffprobe after remuxing

## Practical command patterns

### Verify the remuxed output

```bash
ffprobe -v error -show_entries stream=index,codec_type,codec_name -of default=nw=1 output.mkv
```
