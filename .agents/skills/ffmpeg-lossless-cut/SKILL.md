---
name: ffmpeg-lossless-cut
description: recommend preservation-first ffmpeg commands for users who paste ffprobe, ffprobe -show_packets, mediainfo, or keyframe metadata and want to trim or cut a video segment without unnecessary re-encoding. use when chatgpt needs to decide whether stream-copy cutting is acceptable, when an accurate cut requires re-encoding near the boundary, how to handle keyframe alignment, and to return ready-to-run linux terminal commands with explicit warnings about cut-point inaccuracy.
---

# Ffmpeg Lossless Cut

## Overview

Help the user remove or keep a time range of a video with the least possible quality loss. Stream copy is preferred when the user can tolerate keyframe-aligned cut points. Re-encoding is only recommended when frame-accurate boundaries matter or the container cannot be cut safely.

## Workflow

1. Read the pasted metadata carefully.
2. Extract the facts that materially affect cutting:
   - container
   - video codec and profile
   - audio codec
   - duration and start time offset
   - frame rate
   - keyframe interval evidence when present
   - presence of B-frames or open GOPs when known
3. Classify the cut requirement:
   - **keyframe-tolerant** when the user accepts a cut near the nearest keyframe
   - **frame-accurate** when the user needs an exact start or end time
   - **uncertain** when the request wording does not make this clear
4. Choose one recommendation path:
   - **stream copy** for keyframe-tolerant cuts
   - **smart re-encode** for frame-accurate cuts
5. Return a concise assessment, one recommended command, a short explanation, and warnings.

## Command-building rules

### 1) Stream-copy cut

Use stream copy only when keyframe-aligned boundaries are acceptable. Prefer `-ss` before input for fast seeking, and use an explicit duration rather than mixing absolute `-to` timestamps with input seeking.

```bash
start='00:01:30.000'
duration='00:02:40.000'
ffmpeg -ss "$start" -i "input.ext" -t "$duration" \
  -map 0 -c copy -avoid_negative_ts make_zero \
  "output-cut.mkv"
```

`-map 0` is appropriate only when all streams can be copied into the chosen container. Otherwise map intended streams explicitly. A stream-copy cut may begin or end at a nearby keyframe; inspect the result.

### 2) Frame-accurate video boundary

When accurate video boundaries matter, seek after `-i` and re-encode the video. This decodes from the beginning and can be slow. Copy audio only if its boundary tolerance is acceptable; encode audio when sample-accurate audio trimming is required.

```bash
start='00:01:30.000'
duration='00:02:40.000'
ffmpeg -i "input.ext" -ss "$start" -t "$duration" \
  -map 0:v:0 -map '0:a?' -map '0:s?' \
  -c:v libx264 -preset slow -crf 18 -c:a copy -c:s copy \
  "output-cut.mkv"
```

Do not call a lossy CRF encode lossless. Choose audio handling from the actual source and boundary requirements; converting lossy audio to FLAC does not restore quality.

### 3) Container and stream rules

Use MKV when copied streams are not known to be supported by another target. Preserve chapters and metadata when useful. Never silently omit streams: state exactly which streams the command maps.

## Output format

Use exactly these labels in this order:

### Source assessment
- Summarize the source in 3 to 6 short bullets.
- State whether the cut should be keyframe-tolerant, frame-accurate, or uncertain, and why.
- State whether keyframe interval evidence is present, weak, or absent.

### Recommended command
- Return one ready-to-run FFmpeg command in a fenced bash block.
- Use descriptive placeholder filenames if the real path is not provided.

### Why this command
- Explain the reasoning in 2 to 5 bullets.
- Mention seek placement, stream copy versus re-encode, container choice, audio handling, and timestamp handling.

### Warnings
- Warn that stream-copy cuts are constrained by keyframe/timestamp behavior and are not frame-accurate; verify actual boundaries.
- Warn that re-encoding introduces generation loss unless a lossless codec is chosen.
- Warn that timestamps and A/V sync should be checked after cutting.
- Warn against cutting without verifying duration with ffprobe afterwards.

## Decision defaults

When uncertain, prefer the safer path:

- prefer stream copy
- place `-ss` before `-i` for speed unless exactness is required
- keep all streams unless the user names specific ones
- choose mkv output
- avoid re-encoding unless exactness or compatibility demands it
- preserve timestamps only when the user asks

## Practical command patterns

### Verify the result

```bash
ffprobe -v error -show_entries format=duration,start_time -of default=nw=1 output_cut.mkv
```

### List keyframes near a boundary

```bash
ffprobe -v error -select_streams v:0 -skip_frame nokey \
  -show_entries frame=pts_time -of csv=p=0 input.ext | head -50
```
