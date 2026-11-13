---
name: ffmpeg-subtitle-handle
description: recommend preservation-first ffmpeg commands for users who paste ffprobe or mediainfo metadata and want to extract, convert, or burn in subtitles. use when chatgpt needs to check subtitle codec compatibility, choose stream copy versus SRT conversion, warn about image-based subtitles needing OCR, and return ready-to-run linux terminal commands with warnings about forced subtitles, missing fonts, and irreversible burn-in.
---

# Ffmpeg Subtitle Handle

## Overview

Move subtitles between containers, extract them, or burn them into video, while preserving everything that can be preserved. Image-based subtitles cannot be converted to text without OCR. Burn-in is always destructive to the video.

## Workflow

1. Read the pasted metadata carefully.
2. Extract the facts that materially affect subtitles:
   - subtitle stream indices
   - subtitle codecs (`subrip`, `ass`, `hdmv_pgs_subtitle`, `dvd_subtitle`, `mov_text`)
   - language and title tags
   - whether any track is marked forced or default
   - video codec and container
3. Classify the goal:
   - **extract** when the user wants subtitles as separate files
   - **convert** when the user wants a different text subtitle format
   - **burn in** when the user wants subtitles visible in the picture
   - **uncertain** when the goal is not stated
4. Choose one recommendation path based on the goal and codec.
5. Return a concise assessment, one recommended command, a short explanation, and warnings.

## Command-building rules

### 1) Extract or convert text subtitles

Map the intended stream using its zero-based subtitle-stream ordinal. Copy only when the output container/format supports the source subtitle codec. For text conversion to SRT:

```bash
ffmpeg -i "input.mkv" -map 0:s:0 -c:s srt "subtitle-0.srt"
```

ASS/SSA to SRT loses styling, positioning, and some layout. Do not give a file an extension that does not match the actual subtitle codec.

### 2) Image-based subtitles

PGS and VobSub are image-based and cannot become text SRT without OCR. Keep them in a compatible container or use a tool/format known to extract that exact codec; do not assume FFmpeg can write a standalone `.sup`/`.idx` pair for every input.

### 3) Burn in subtitles

Only when explicitly requested. Select the correct subtitle stream, ensure the subtitle filter can read it, and test fonts/rendering. Burn-in permanently changes video pixels and re-encodes video.

```bash
ffmpeg -i "input.mkv" -map 0:v:0 -map '0:a?' \
  -vf "subtitles=input.mkv:si=0" -c:v libx264 -preset slow -crf 18 \
  -c:a copy "output-burned.mkv"
```

Check FFmpeg subtitle-stream index semantics for the input and escape paths containing colons or special characters. Do not automatically burn a forced track; confirm the intended track with the user. Preserve or explicitly omit other subtitle tracks and explain the mapping.

## Output format

Use exactly these labels in this order:

### Source assessment
- Summarize subtitle streams in 3 to 6 short bullets.
- State whether each stream is text-based or image-based.
- State whether burn-in would be required or optional.

### Recommended command
- Return one ready-to-run FFmpeg command in a fenced bash block.
- For multiple streams, return one fenced block with each command on its own line.

### Why this command
- Explain the reasoning in 2 to 5 bullets.
- Mention stream mapping, codec choice, container compatibility, and whether video is re-encoded.

### Warnings
- Always warn that burn-in re-encodes video and is irreversible.
- Warn that image-based subtitles require OCR to become text.
- Warn about missing fonts and styling for ASS burn-in.
- Warn that converting ASS to SRT loses styling.
- Warn about forced subtitle semantics.

## Decision defaults

When uncertain, prefer the safer path:

- extract rather than burn in
- stream copy when format-compatible
- MKV output
- never OCR without an explicit request
- never burn in without confirmation

## Practical command patterns

### List subtitle streams

```bash
ffprobe -v error -select_streams s \
  -show_entries stream=index,codec_name:stream_tags=language,title:stream_disposition=forced,default \
  -of default=nw=1 input.ext
```
