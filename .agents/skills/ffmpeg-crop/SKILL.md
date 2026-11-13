---
name: ffmpeg-crop
description: recommend preservation-first ffmpeg commands for users who paste cropdetect, ffprobe, or mediainfo metadata and want to remove black bars or unwanted edges. use when chatgpt needs to validate cropdetect output, apply even-dimension rounding, preserve aspect ratio after cropping, and return ready-to-run linux terminal commands with warnings about over-cropping, letterbox detection false positives, and mandatory visual confirmation.
---

# Ffmpeg Crop

## Overview

Crop only when the user explicitly wants it and only when the evidence is trustworthy. cropdetect is suggestive, not definitive. Cropping requires video re-encoding; a typical lossy encode reduces quality, while lossless encoding still changes the frame geometry.

## Workflow

1. Read the pasted metadata carefully.
2. Extract the facts that materially affect cropping:
   - width and height
   - display aspect ratio and sample aspect ratio
   - cropdetect output when present
   - letterbox or pillarbox evidence
   - video codec and bit depth
3. Classify the crop evidence:
   - **strong** when cropdetect agrees across multiple samples and the result is plausible for the content
   - **weak** when cropdetect is single-sample, unstable, or produces an implausible box
   - **absent** when cropdetect was not provided
4. Choose one recommendation path:
   - **crop with visual verification** when evidence is strong and the user asked
   - **decline to crop** when evidence is weak or absent
5. Return a concise assessment, one recommended command, a short explanation, and warnings.

## Command-building rules

### 1) Measure multiple sections

```bash
ffmpeg -ss 00:05:00 -i "input.ext" -map 0:v:0 \
  -vf "cropdetect=24:16:0" -frames:v 300 -an -f null -
```

Run at multiple representative timestamps. Cropdetect is evidence, not proof; preview the crop against real scenes and confirm no picture content is removed.

### 2) Apply a confirmed crop

```bash
ffmpeg -i "input.ext" -map 0:v:0 -map '0:a?' -map '0:s?' \
  -vf "crop=1920:800:0:140,setsar=1" \
  -c:v libx264 -preset slow -crf 18 -c:a copy -c:s copy "output-cropped.mkv"
```

Replace example dimensions/offsets with confirmed values from the user's source. Ensure crop dimensions and offsets satisfy the selected codec/pixel format (often even values for 4:2:0). Cropping requires video re-encoding. Preserve intended audio/subtitle streams and warn if a mapping drops anything.

### 3) Crop then resize

Only add scaling/padding when a target canvas is explicitly requested. Validate the cropped display aspect ratio first; padding changes framing but does not stretch. Do not use a fixed crop from an example as though it were detected from the user's file.

## Output format

Use exactly these labels in this order:

### Source assessment
- Summarize the source in 3 to 6 short bullets.
- State whether crop evidence is strong, weak, or absent, and why.
- State the implied aspect ratio after cropping.

### Recommended command
- Return the measurement command and the crop command in one fenced bash block, clearly labeled.
- Use descriptive placeholder filenames if the real path is not provided.

### Why this command
- Explain the reasoning in 2 to 5 bullets.
- Mention cropdetect evidence, even dimensions, aspect ratio, and re-encode necessity.

### Warnings
- Always warn against blind cropping when cropdetect is absent or weak.
- Warn that visual confirmation is mandatory.
- Warn that cropping requires video re-encoding and changes framing; explain encoding loss when using a lossy codec.
- Warn that over-cropping removes picture content.
- Warn against stretching after cropping.

## Decision defaults

Do not crop unless requested and supported by stable multi-sample evidence plus visual confirmation. Use source-specific crop values, check display aspect ratio and codec alignment, and explain video re-encoding.

## Practical command patterns

### Verify crop result before encoding

```bash
ffmpeg -ss 00:05:00 -i input.ext -vf "crop=1920:800:0:140" -frames:v 1 preview.png
```
