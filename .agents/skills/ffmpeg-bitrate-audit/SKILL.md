---
name: ffmpeg-bitrate-audit
description: Analyze supplied FFprobe or MediaInfo data to contextualize video bitrate and bits per pixel per frame. Use when deciding whether bitrate suggests an encoding concern or when selecting CRF settings for an explicitly requested encode; explain that codec, content, and encoder settings prevent universal thresholds.
---

# Ffmpeg Bitrate Audit

## Overview

Audit bitrate relative to resolution, frame rate, and codec, then recommend encode settings. Bitrate alone is meaningless without resolution, frame rate, and codec context. CRF is preferred over fixed bitrate targets for preservation-first encoding.

## Workflow

1. Read the pasted metadata carefully.
2. Extract the facts that materially affect the audit:
   - video codec and profile
   - width and height
   - frame rate
   - overall and video bitrate
   - pixel format and bit depth
   - duration
3. Compute bits per pixel per frame (bpp):

```text
bpp = video_bitrate / (width * height * frame_rate)
```

4. Classify the source:
   - **context only** when enough data exists for a rough bpp calculation
   - **uncertain** when bitrate, dimensions, or frame-rate evidence is missing
5. Choose one recommendation path:
   - **re-encode with CRF** for practical quality
   - **no re-encode** when the source is already efficient
6. Return a concise assessment, one recommended command, a short explanation, and warnings.

## Command-building rules

### 1) Compute a screening metric

If video bitrate, dimensions, and a representative average frame rate are available, calculate:

```text
bits per pixel per frame = video_bitrate / (width × height × average_frame_rate)
```

Use the stream video bitrate, not total container bitrate, where possible. If bitrate is missing or only an overall bitrate is reported, state that the calculation is unavailable or approximate. BPP is only a screening metric: codec generation, encoder settings, grain, motion, animation, bit depth, chroma format, and VFR all affect quality. Do not classify a file as over/under-encoded from a universal numeric threshold.

### 2) Decide whether an encode is justified

Do not re-encode just because bitrate is high. If no size/compatibility goal exists and the source looks acceptable, recommend keeping it. Re-encoding a lossy source adds generation loss. If the user requests an encode, select a compatible encoder and pixel format; use CRF only as a quality/size tradeoff, not as proof of better quality.

```bash
ffmpeg -i "input.ext" -map 0:v:0 -map '0:a?' -map '0:s?' \
  -c:v libx264 -preset slow -crf 18 -c:a copy -c:s copy "output.mkv"
```

Adapt mappings and codecs to the actual streams and target container. Do not use `-map 0` with a codec combination that cannot encode every mapped stream.

### 3) Lossless derivative

Use FFV1 only when the user explicitly wants a lossless encoded derivative and file size is acceptable. Lossless encoding does not restore quality from lossy input. Preserve compatible audio by stream copy when possible; converting audio to FLAC is optional, not inherently beneficial.

## Output format

Use exactly these labels in this order:

### Source assessment
- Summarize the source in 3 to 6 short bullets.
- Show the computed bpp.
- State what the metric can and cannot establish; do not label the encode quality from bpp alone.

### Recommended command
- Return one ready-to-run FFmpeg command in a fenced bash block.
- Use descriptive placeholder filenames if the real path is not provided.

### Why this command
- Explain the reasoning in 2 to 5 bullets.
- Mention bpp, codec, CRF choice, audio handling, and container choice.

### Warnings
- Always warn that bitrate targets are content-dependent.
- Warn that CRF does not guarantee a file size.
- Warn that re-encoding a lossy source adds generation loss.
- Warn that bpp ranges are rough guidance, not rules.

## Decision defaults

When uncertain, prefer the safer path:

- compute bpp before recommending anything
- CRF over fixed bitrate
- copy audio when practical
- MKV output
- no denoise, sharpening, or resolution changes

## Practical command patterns

### Measure bitrate and frame rate

```bash
ffprobe -v error -select_streams v:0 \
  -show_entries stream=codec_name,width,height,r_frame_rate,bit_rate,pix_fmt \
  -show_entries format=bit_rate,duration \
  -of default=nw=1 input.ext
```
