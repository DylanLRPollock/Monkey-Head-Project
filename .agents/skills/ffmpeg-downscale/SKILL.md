---
name: ffmpeg-downscale
description: recommend preservation-first ffmpeg commands for users who paste ffprobe or mediainfo metadata and want a smaller 720p or 480p derivative without distortion. use when chatgpt needs to choose target resolution, preserve display aspect ratio with scaling and padding, decide audio and container handling for a smaller output, and return ready-to-run linux terminal commands with warnings about quality loss and unnecessary upscaling.
---

# Ffmpeg Downscale

## Overview

Produce a smaller-resolution derivative without distortion. Downscaling is generally safe when done with a good scaler and no unnecessary re-quantization. Upscaling a smaller source to a downscale target is pointless and must be refused or flagged.

## Workflow

1. Read the pasted metadata carefully.
2. Extract the facts that materially affect downscaling:
   - width and height
   - display aspect ratio and sample aspect ratio
   - video codec and bit depth
   - frame rate
   - field order or interlace evidence
   - audio codec
   - color metadata
3. Classify the source:
   - **downscale** when fitting to the requested target reduces displayed source dimensions
   - **would upscale** when the requested target enlarges the source
   - **equal or mixed** when source dimensions match one target dimension or aspect ratios require padding
4. Choose one recommendation path:
   - **safe downscale** for most cases
   - **preserve source size or ask** when the requested output would enlarge it
5. Return a concise assessment, one recommended command, a short explanation, and warnings.

## Command-building rules

### 1) Resolution and framing

Use 1280×720 only when it is the requested target or a suitable delivery size. Preserve display aspect ratio with fit-and-pad framing; never stretch. Set square pixels only when appropriate for the source.

```bash
-vf "scale=1280:720:flags=lanczos:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1"
```

Check sample/display aspect ratio before applying the pattern, especially for anamorphic sources.

### 2) Do not upscale by accident

Compare the source's display dimensions with the requested target. If producing the target canvas would enlarge the source, do not call that a downscale; recommend keeping the source size or ask for a smaller target. Mixed-aspect sources may require padding even when one source dimension is smaller.

### 3) Interlace and video encoding

Deinterlace only with clear field-order or `idet` evidence; otherwise preserve scan structure. A practical H.264 derivative may use `libx264 -preset slow -crf 20`, but choose pixel format/bit depth from the source and intended playback. Do not silently reduce 10-bit or unusual chroma formats. FFV1 can make a lossless filtered derivative, but scaling still changes the picture and may not reduce size.

### 4) Audio and container

Copy audio when compatible with the output container. Do not convert lossy or unknown audio to FLAC by default. Use MKV for broad stream compatibility, or another container only when the delivery target requires it. Preserve known color metadata and do not invent missing tags.

## Output format

Use exactly these labels in this order:

### Source assessment
- Summarize the source in 3 to 6 short bullets.
- State whether downscaling is meaningful, equal, or pointless upscaling.
- State whether interlacing is present, absent, or uncertain.

### Recommended command
- Return one ready-to-run FFmpeg command in a fenced bash block.
- Use descriptive placeholder filenames if the real path is not provided.

### Why this command
- Explain the reasoning in 2 to 5 bullets.
- Mention scaling, padding, codec choice, audio handling, and container choice.

### Warnings
- Always warn against stretching.
- Warn against deinterlacing when the source is progressive or uncertain.
- Warn that lossy re-encoding reduces quality.
- Warn when the source is already at or below the target resolution.
- Warn against cropping without visual confirmation.

## Decision defaults

Check display aspect ratio and whether the requested output would enlarge any source detail. Preserve framing with fit-and-pad, do not stretch or crop by default, and do not silently reduce bit depth/chroma or transcode audio.

## Practical command patterns

### Check aspect ratio before choosing padding

```bash
ffprobe -v error -select_streams v:0 \
  -show_entries stream=width,height,sample_aspect_ratio,display_aspect_ratio,r_frame_rate \
  -of default=nw=1 input.ext
```
