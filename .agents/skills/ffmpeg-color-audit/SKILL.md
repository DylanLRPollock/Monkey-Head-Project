---
name: ffmpeg-color-audit
description: recommend preservation-first ffmpeg commands for users who paste ffprobe or mediainfo metadata and want to audit or fix color tagging without changing the picture. use when chatgpt needs to identify missing or inconsistent color metadata, decide whether to carry tags through, distinguish tagging fixes from real color transforms, and return ready-to-run linux terminal commands with warnings about mis-tagging causing playback errors.
---

# Ffmpeg Color Audit

## Overview

Audit color metadata and carry it through correctly. Tagging fixes are cheap and reversible in intent, but a wrong tag on the wrong picture can look worse than no tag. Never perform an actual color transform under the label of a tag fix.

## Workflow

1. Read the pasted metadata carefully.
2. Extract the color facts:
   - color range (`tv` or `pc`)
   - color space
   - color transfer
   - color primaries
   - pixel format and bit depth
3. Classify the source:
   - **fully tagged** when all four fields are present and consistent
   - **partially tagged** when some fields are missing
   - **untagged** when none are present
   - **inconsistent** when fields contradict the pixel format or codec profile
4. Choose one recommendation path:
   - **carry tags through** for fully tagged sources
   - **request evidence** for partially tagged or untagged sources; do not guess missing values
   - **decline** when the evidence is contradictory
5. Return a concise assessment, one recommended command, a short explanation, and warnings.

## Command-building rules

### 1) Preserve known tags

For an unchanged stream, retain existing metadata with stream copy when the target muxer supports it. A generic `-map_metadata 0` copies metadata dictionaries; it does not guarantee codec-level color signaling is preserved or corrected.

### 2) Correct tags only with evidence

Only propose values supported by reliable source information or an explicit user decision. For an encode, output color options may set signaling such as `-color_primaries`, `-color_trc`, `-colorspace`, and `-color_range`; these options do not transform pixels. Stream-copy tag changes are container/codec-specific, so verify the exact output with ffprobe and the target playback path.

Do not set BT.709 merely because video is SDR or 10-bit. Do not infer limited/full range, primaries, transfer, or matrix from bit depth alone. If pixel values need a color transform, describe that as a separate operation and explain its loss/risks before giving a transform command.

## Output format

Use exactly these labels in this order:

### Source assessment
- Summarize the color metadata in 3 to 6 short bullets.
- State whether the source is fully tagged, partially tagged, untagged, or inconsistent.
- State whether a tag fix is safe or whether a transform is needed.

### Recommended command
- Return one ready-to-run FFmpeg command in a fenced bash block.
- Use descriptive placeholder filenames if the real path is not provided.

### Why this command
- Explain the reasoning in 2 to 5 bullets.
- Mention which tags are present, which are assumed, and why no filter is used.

### Warnings
- Always warn that wrong tags can cause playback to look washed out or crushed.
- Warn that tag fixes do not change pixel data.
- Warn that transforms are a different operation and require confirmation.
- Warn against inventing missing color values.

## Decision defaults

When uncertain, prefer the safer path:

- carry existing tags through
- do not add missing tags without labeling the assumption
- do not transform color
- stream copy when possible
- MKV output

## Practical command patterns

### Audit color fields

```bash
ffprobe -v error -select_streams v:0 \
  -show_entries stream=pix_fmt,color_range,color_space,color_transfer,color_primaries \
  -of default=nw=1 input.ext
```
