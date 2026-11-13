---
name: ffmpeg-thumbnails
description: recommend preservation-first ffmpeg commands for users who paste ffprobe or mediainfo metadata and want a contact sheet, thumbnail grid, or representative stills from a video. use when chatgpt needs to choose a sampling interval, avoid blank or duplicated frames, preserve aspect ratio in thumbnails, and return ready-to-run linux terminal commands with warnings about black frames, seek accuracy, and large tile images.
---

# Ffmpeg Thumbnails

## Overview

Generate thumbnail grids or stills without touching the source video. Sampling choices matter more than encoder settings. Avoid the first frames of a file, which are often black.

## Workflow

1. Read the pasted metadata carefully.
2. Extract the facts that materially affect sampling:
   - duration
   - frame rate
   - resolution
   - field order
   - chapter timestamps when present
3. Classify the request:
   - **contact sheet** when the user wants a grid
   - **single still** when the user wants one frame
   - **interval stills** when the user wants one image per N seconds
   - **uncertain** when the goal is not stated
4. Choose one recommendation path.
5. Return a concise assessment, one recommended command, a short explanation, and warnings.

## Command-building rules

### 1) Contact sheet

Choose the sample interval from clip duration and the desired number of cells. `fps=1/60` plus a 5×4 tile makes a sheet for the first 20 sampled frames only; it does not automatically summarize an arbitrarily long video. For a 20-cell sheet, calculate a rate that covers the desired interval, and keep the tile count manageable.

```bash
ffmpeg -i "input.ext" \
  -vf "fps=1/60,scale=320:-1:flags=lanczos,tile=5x4" \
  -frames:v 1 "contact-sheet.png"
```

Adapt the rate, tile dimensions, and sampling start to the clip length. Use timestamps or chapter boundaries when representative coverage matters. Scaling with `-1` preserves aspect ratio; do not enlarge beyond source detail.

### 2) Interval stills

```bash
ffmpeg -i "input.ext" -vf "fps=1/30,scale=640:-1:flags=lanczos" \
  -fps_mode vfr "still-%04d.png"
```

Warn that long clips create many files. Use `-fps_mode vfr` only when avoiding duplicate output timestamps/frames is appropriate.

### 3) One still

For an accurate timestamp, place `-ss` after `-i` (slower, frame-accurate decode); placing it before `-i` is faster but may seek to a nearby keyframe.

```bash
ffmpeg -i "input.ext" -ss 00:02:00 -frames:v 1 "still.png"
```

Use JPEG only when lossy still output is acceptable. Very large contact sheets can consume substantial memory.

## Output format

Use exactly these labels in this order:

### Source assessment
- Summarize the source in 3 to 6 short bullets.
- State the duration and the recommended sampling interval.
- State whether the opening is likely black.

### Recommended command
- Return one ready-to-run FFmpeg command in a fenced bash block.
- Use descriptive placeholder filenames if the real path is not provided.

### Why this command
- Explain the reasoning in 2 to 5 bullets.
- Mention sampling rate, tile size, scaling, and output format.

### Warnings
- Warn about black or blank frames at the start.
- Warn about seek accuracy when using `-ss` before `-i`.
- Warn that very large grids consume memory.
- Warn against upscaling thumbnails.

## Decision defaults

Choose samples using clip duration and desired coverage. Preserve aspect ratio, avoid unnecessary upscaling, and make sure the tile count can cover the intended interval. Place seek after input for accurate still timestamps.

## Practical command patterns

### Get duration before choosing a grid

```bash
ffprobe -v error -show_entries format=duration -of default=nw=1 input.ext
```
