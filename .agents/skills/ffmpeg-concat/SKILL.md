---
name: ffmpeg-concat
description: recommend preservation-first ffmpeg commands for users who paste ffprobe, mediainfo, or stream metadata for two or more files and want to join them safely. use when chatgpt needs to decide whether stream-copy concatenation is valid, when codecs, resolutions, sample rates, or timebases differ, when the concat demuxer versus concat filter applies, and to return ready-to-run linux terminal commands with warnings about A/V desync and silent corruption.
---

# Ffmpeg Concat

## Overview

Join multiple media files with the least processing that is still correct. The concat demuxer with `-c copy` is preferred only when all streams match. When streams differ, the concat filter is required and re-encoding is unavoidable.

## Workflow

1. Read the pasted metadata for every input.
2. Compare the facts that must match for safe stream-copy concat:
   - container
   - video codec and profile
   - resolution and pixel format
   - frame rate and timebase
   - audio codec, sample rate, channel layout
   - number of streams
   - color metadata
3. Classify the join:
   - **compatible** when all required fields match
   - **incompatible** when codec, resolution, sample rate, or timebase differ
   - **uncertain** when any required field is missing from the metadata
4. Choose one recommendation path:
   - **concat demuxer with stream copy** for compatible inputs
   - **concat filter with re-encode** for incompatible or uncertain inputs
5. Return a concise assessment, one recommended command, a short explanation, and warnings.

## Command-building rules

### 1) Concat demuxer with stream copy

Use only when corresponding streams are compatible across all inputs: same stream order and types, compatible codec parameters, time bases, and relevant audio layouts. Container names alone do not determine compatibility.

```bash
printf "file '%s'
" "part1.mkv" "part2.mkv" > concat-list.txt
ffmpeg -f concat -safe 0 -i concat-list.txt -map 0 -c copy "joined.mkv"
```

Use trusted paths with `-safe 0`; escape quotes and special characters in concat-list paths, or ask for simple filenames. Confirm all streams in the result. If any required stream differs, do not imply that stream copy is safe.

### 2) Concat filter and re-encode

Use a concat filter only when inputs need normalization. It requires matching filter outputs: same video dimensions, pixel format, frame rate/time base, and audio sample rate/channel layout. Build branches only for streams present in every input. Pick a target size and frame rate based on the user request and inputs; do not force 1080p or 48 kHz without reason. Re-encoding changes quality. Map only the filtered outputs and any intentionally copied streams.

### 3) Audio and timestamps

Copy audio only when codecs, layouts, and timing are compatible and the filter path permits it. If audio must be filtered, use an appropriate common sample rate and layout, and explain the conversion. Investigate timestamp gaps or offsets before using `-fflags +genpts`; it is not a general-purpose repair flag. Do not chain many inputs without warning about processing time.

## Output format

Use exactly these labels in this order:

### Source assessment
- Summarize each input in 1 to 2 short bullets.
- State whether the inputs are compatible, incompatible, or uncertain, and why.
- State which specific fields matched and which did not.

### Recommended command
- Return one ready-to-run FFmpeg command in a fenced bash block.
- Include the list-file creation line when the concat demuxer is used.

### Why this command
- Explain the reasoning in 2 to 5 bullets.
- Mention demuxer versus filter choice, codec handling, audio handling, and container choice.

### Warnings
- Warn that incompatible streams can make the concat demuxer fail or produce unreliable output; inspect the logs and verify the result.
- Warn about A/V desync from timestamp discontinuities.
- Warn that the concat filter re-encodes and therefore introduces generation loss.
- Warn against mixing frame rates without a stated reason.

## Decision defaults

When uncertain, prefer the safer path:

- verify all fields before recommending stream copy
- prefer the concat demuxer when fields match
- prefer the concat filter when any field is unknown
- choose mkv output
- choose flac for audio when re-encoding
- preserve the majority frame rate

## Practical command patterns

### Inspect all inputs before joining

```bash
for f in part1.mkv part2.mkv; do
  ffprobe -v error -show_entries stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels \
    -of default=nw=1 "$f"
done
```
