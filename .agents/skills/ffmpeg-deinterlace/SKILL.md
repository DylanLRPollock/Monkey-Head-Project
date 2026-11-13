---
name: ffmpeg-deinterlace
description: recommend preservation-first ffmpeg commands for users who paste ffprobe, idet, or mediainfo field-order metadata and want to remove interlacing correctly. use when chatgpt needs to distinguish true interlacing from telecined film, choose between bwdif, yadif, and fieldmatch plus decimate, preserve frame rate, and return ready-to-run linux terminal commands with warnings about deinterlacing progressive or telecined sources.
---

# Ffmpeg Deinterlace

## Overview

Remove combing from genuinely interlaced sources. Interlaced and telecined sources require different handling. Deinterlacing a progressive or telecined source destroys quality.

## Workflow

1. Read the pasted metadata carefully.
2. Extract the facts that materially affect deinterlacing:
   - field order
   - idet output when present
   - frame rate
   - source origin if stated
   - resolution
   - codec
3. Classify the source:
   - **interlaced** when field order and idet clearly agree
   - **telecined** when idet shows a repeating pattern of 4 progressive and 1 combed frame at ~29.97 fps
   - **progressive** when field order is progressive and idet shows no combing
   - **uncertain** when the evidence is weak or conflicting
4. Choose one recommendation path:
   - **bwdif deinterlace** for true interlaced
   - **inverse telecine** for telecined film
   - **no processing** for progressive or uncertain sources
5. Return a concise assessment, one recommended command, a short explanation, and warnings.

## Command-building rules

### 1) Measure before changing frames

```bash
ffmpeg -i "input.ext" -map 0:v:0 -vf idet -frames:v 500 -an -f null -
```

Use a representative section, not just the opening frames. Treat metadata and `idet` as evidence; inspect difficult or mixed content visually.

### 2) Genuine interlace

Only when evidence supports true interlace, deinterlace before any other spatial scaling. `send_frame` retains approximately the input frame rate; `send_field` doubles output frame rate and changes cadence.

```bash
ffmpeg -i "input.ext" -map 0:v:0 -map '0:a?' -map '0:s?' \
  -vf "bwdif=mode=send_frame:parity=auto:deint=all" \
  -c:v libx264 -preset slow -crf 18 -c:a copy -c:s copy "output-deinterlaced.mkv"
```

Choose pixel format and additional mappings based on source streams. Avoid `-map 0` if unrelated video/data streams should not be encoded or cannot be copied.

### 3) Telecine

Use `fieldmatch,decimate` only when a stable film cadence is clearly established and the source is not mixed/edited interlace. Test a short representative segment first; inverse telecine can fail on mixed content. For progressive or uncertain material, recommend no deinterlacing.

## Output format

Use exactly these labels in this order:

### Source assessment
- Summarize the field-order and idet evidence in 3 to 6 short bullets.
- State whether the source is interlaced, telecined, progressive, or uncertain, and why.
- State whether the evidence is strong, weak, or conflicting.

### Recommended command
- Return one ready-to-run FFmpeg command in a fenced bash block.
- Use descriptive placeholder filenames if the real path is not provided.
- Include the idet measurement command when it is not already present.

### Why this command
- Explain the reasoning in 2 to 5 bullets.
- Mention field order, idet results, deinterlacer choice, frame rate handling, and audio handling.

### Warnings
- Always warn against deinterlacing progressive or uncertain sources.
- Warn that IVTC can break on mixed content.
- Warn that deinterlacing is lossy and irreversible.
- Warn that `send_field` changes frame rate.

## Decision defaults

When uncertain, prefer the safer path:

- no deinterlace
- run idet first when evidence is missing
- `bwdif` over other filters for true interlaced
- `parity=auto` over hardcoded field order
- preserve frame rate
- copy audio

## Practical command patterns

### Read idet counts

```bash
ffmpeg -i input.ext -vf idet -frames:v 500 -an -f null - 2>&1 | grep -E "frame|Repeated|Multi"
```
