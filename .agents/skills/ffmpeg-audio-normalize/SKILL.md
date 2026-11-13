---
name: ffmpeg-audio-normalize
description: recommend preservation-first ffmpeg commands for users who paste ffprobe, loudnorm, or ebur128 metadata and want to normalize loudness without ruining dynamics. use when chatgpt needs to choose EBU R128 two-pass loudnorm settings, decide between peak normalization and loudness normalization, preserve lossless audio, and return ready-to-run linux terminal commands with warnings about generation loss and over-compression.
---

# Ffmpeg Audio Normalize

## Overview

Normalize audio to a consistent perceived loudness using EBU R128 two-pass loudnorm. Peak normalization alone is only recommended when the user wants to avoid clipping without changing perceived loudness.

## Workflow

1. Read the pasted metadata carefully.
2. Extract the facts that materially affect normalization:
   - audio codec
   - sample rate and channel layout
   - whether the source is lossless
   - any loudnorm or ebur128 measurement already provided
   - target platform or delivery spec when stated
3. Classify the goal:
   - **loudness normalization** when the user wants consistent perceived level
   - **peak limiting** when the user only wants to control peaks
   - **uncertain** when the goal is not stated
4. Choose one recommendation path:
   - **two-pass loudnorm** for loudness normalization
   - **limiting** only when the user wants peak control, not loudness matching
5. Return a concise assessment, one recommended command, a short explanation, and warnings.

## Command-building rules

### 1) Two-pass loudness normalization

Choose target integrated loudness from the stated delivery requirement. For general web or speech use, `I=-16` may be a reasonable starting point; use the specified platform/broadcast target when provided. Do not present one target as universal.

Measurement pass:

```bash
ffmpeg -i "input.ext" -map 0:a:0 \
  -af "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json" -f null -
```

Apply the actual `input_i`, `input_tp`, `input_lra`, `input_thresh`, and `target_offset` values reported by measurement:

```bash
ffmpeg -i "input.ext" -map '0:v?' -map 0:a:0 -map '0:s?' \
  -af "loudnorm=I=-16:TP=-1.5:LRA=11:measured_I=-23.0:measured_TP=-2.1:measured_LRA=7.0:measured_thresh=-33.0:offset=0.0:linear=true:print_format=summary" \
  -c:v copy -c:a flac -c:s copy "output-normalized.mkv"
```

Replace every placeholder with measured numeric output; do not run the example literally. If linear mode cannot meet the targets, FFmpeg may use dynamic processing; explain that behavior. FLAC is lossless for the decoded result but does not recover quality lost in a lossy source.

### 2) Peak limiting

Peak limiting is not loudness normalization. Use a limiter only when the user asks to control peaks, and choose a ceiling for the intended delivery. Do not describe a fixed `volume` multiplier as normalization.

### 3) Video and audio handling

Map only streams that should be retained. Copy video when no video changes are needed. Normalization necessarily processes and re-encodes audio; choose FLAC only for an appropriate MKV/lossless workflow, or a target-compatible codec when delivery requires it. Preserve sample rate and channel layout unless there is a reason to change them.

## Output format

Use exactly these labels in this order:

### Source assessment
- Summarize the audio in 3 to 6 short bullets.
- State whether the source audio is lossless or lossy.
- State whether a prior loudnorm or ebur128 measurement is available.

### Recommended command
- Return the first-pass measurement command and the second-pass apply command in one fenced bash block, clearly labeled.
- Use descriptive placeholder filenames if the real path is not provided.

### Why this command
- Explain the reasoning in 2 to 5 bullets.
- Mention two-pass loudnorm, target values, audio codec choice, and video copy.

### Warnings
- Always warn that normalization re-encodes audio unless the user accepts a stream copy, which cannot normalize.
- Warn that loudnorm with `linear=false` can reduce dynamic range.
- Warn that peak normalization does not equal loudness normalization.
- Warn to verify with a second loudnorm measurement pass.

## Decision defaults

When uncertain, prefer the safer path:

- two-pass loudnorm over one-pass
- `linear=true` to preserve dynamics
- `I=-16`, `TP=-1.5`, `LRA=11`
- FLAC audio in MKV
- `-c:v copy` for video
- preserve sample rate and channel layout

## Practical command patterns

### Verify the result

```bash
ffmpeg -i output_normalized.mkv -af loudnorm=I=-16:TP=-1.5:LRA=11:print_format=summary -f null -
```
