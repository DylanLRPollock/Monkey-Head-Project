---
name: ffmpeg-frame-rate
description: recommend preservation-first ffmpeg commands for users who paste ffprobe, mediainfo, or frame-rate metadata and want to change or verify a video's frame rate. use when chatgpt needs to distinguish constant from variable frame rate, avoid interpolation by default, handle CFR versus VFR output correctly, and return ready-to-run linux terminal commands with warnings about cadence damage and duplicate or dropped frames.
---

# Ffmpeg Frame Rate

## Overview

Frame-rate changes are invasive. Preserve the source frame rate unless the user states a clear reason to change it. Distinguish between retiming metadata, dropping duplicate frames, and true interpolation.

## Workflow

1. Read the pasted metadata carefully.
2. Extract the facts that materially affect frame rate:
   - r_frame_rate and avg_frame_rate (as hints, not proof of CFR/VFR)
   - whether VFR evidence is present
   - duration and frame count
   - timebase
   - field order
   - container
3. Classify the source:
   - **CFR** only when frame timestamp evidence supports constant spacing
   - **VFR** only when per-frame or packet timing shows variable spacing
   - **uncertain** when only nominal rates or incomplete metadata are available
4. Choose one recommendation path:
   - **preserve** for most cases
   - **CFR conversion** when the user needs a constant-rate deliverable
   - **avoid** frame-rate change when the user wants smoother playback without a stated target
5. Return a concise assessment, one recommended command, a short explanation, and warnings.

## Command-building rules

### 1) Preserve by default

If no change is requested and streams are otherwise compatible, use stream copy. This preserves existing frame timestamps; it does not convert VFR to CFR.

```bash
ffmpeg -i "input.ext" -map 0 -c copy "output.mkv"
```

### 2) Audit CFR/VFR

A difference between `r_frame_rate` and `avg_frame_rate` alone does not prove VFR. Inspect frame timestamps or packet durations across the clip and account for container time base and edit lists. Missing metadata means uncertain, not automatically CFR/VFR.

### 3) Convert to CFR only for a stated delivery target

Choose the user/platform target explicitly. A `fps` filter duplicates or drops frames to meet CFR; explain cadence impact. Re-encode video and copy audio only when synchronization/timing is valid.

```bash
ffmpeg -i "input.ext" -map 0:v:0 -map '0:a?' -map '0:s?' \
  -vf "fps=24000/1001" -fps_mode cfr \
  -c:v libx264 -preset slow -crf 18 -c:a copy -c:s copy "output-cfr.mkv"
```

Replace the example rate with the requested target; do not infer it from a nominal rate alone.

### 4) Retiming metadata

Retiming changes playback speed/duration and can alter audio synchronization. Muxer options such as `-video_track_timescale` are container-specific (for example, MP4); they do not convert frame cadence and must not be presented as a general VFR-to-CFR fix. Explain the exact timing change before recommending retiming.

## Output format

Use exactly these labels in this order:

### Source assessment
- Summarize the frame rate evidence in 3 to 6 short bullets.
- State whether the source is CFR, VFR, or uncertain, and why.
- State whether a frame-rate change is warranted.

### Recommended command
- Return one ready-to-run FFmpeg command in a fenced bash block.
- Use descriptive placeholder filenames if the real path is not provided.

### Why this command
- Explain the reasoning in 2 to 5 bullets.
- Mention CFR versus VFR, target rate, filter choice, and audio handling.

### Warnings
- Always warn that frame-rate conversion changes motion cadence.
- Warn that interpolation is not preservation.
- Warn that VFR sources can cause A/V desync if mishandled.
- Warn against rounding fractional frame rates to decimal approximations.

## Decision defaults

When uncertain, prefer the safer path:

- preserve the source frame rate
- do not interpolate
- use fractional frame-rate notation
- copy audio
- use MKV output

## Practical command patterns

### Measure frame rate and VFR evidence

```bash
ffprobe -v error -select_streams v:0 \
  -show_entries stream=r_frame_rate,avg_frame_rate,time_base,nb_frames \
  -of default=nw=1 input.ext
```
