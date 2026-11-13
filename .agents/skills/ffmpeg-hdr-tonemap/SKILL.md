---
name: ffmpeg-hdr-tonemap
description: recommend preservation-first ffmpeg commands for users who paste ffprobe, mediainfo, or color metadata and want to convert HDR video to SDR. use when chatgpt needs to identify PQ or HLG transfer characteristics, choose a conservative tone-mapping chain, preserve or reset color tags correctly, and return ready-to-run linux terminal commands with warnings about approximate color, clipping, and missing HDR metadata.
---

# Ffmpeg Hdr Tonemap

## Overview

Convert HDR to SDR with an explicit, documented tone-mapping chain. Tone mapping is inherently approximate. Preserve the original file when the user has not confirmed they want a converted derivative.

## Workflow

1. Read the pasted metadata carefully.
2. Extract the facts that materially affect tone mapping:
   - color transfer (`smpte2084` or `arib-std-b67`)
   - color primaries (`bt2020`)
   - color space
   - color range
   - bit depth
   - mastering display metadata and content light level when present
   - video codec
3. Classify the source:
   - **PQ HDR** when transfer is `smpte2084`
   - **HLG HDR** when transfer is `arib-std-b67`
   - **SDR** when transfer is `bt709` or similar
   - **uncertain** when color metadata is missing or incomplete
4. Choose one recommendation path:
   - **tone map** for confirmed HDR
   - **decline and request metadata** for uncertain sources
5. Return a concise assessment, one recommended command, a short explanation, and warnings.

## Command-building rules

### 1) Confirm HDR input

Require reliable transfer/primaries metadata or other strong evidence distinguishing PQ (`smpte2084`) from HLG (`arib-std-b67`). Missing/conflicting metadata is not enough to choose a tone curve. Preserve the original HDR master.

### 2) Tone-map to SDR

Tone mapping is a lossy, approximate pixel transform. Use an FFmpeg build with `zscale` and `tonemap`; adapt input transfer/primaries and output range to the source and delivery target. This illustrative chain assumes correctly tagged BT.2020 PQ or HLG input and limited-range BT.709 SDR output; verify against the installed FFmpeg version and test a short clip first.

```bash
ffmpeg -i "input-hdr.mkv" -map 0:v:0 -map '0:a?' -map '0:s?' \
  -vf "zscale=transfer=linear:npl=100,format=gbrpf32le,zscale=primaries=bt709,tonemap=tonemap=hable:desat=0,zscale=transfer=bt709:matrix=bt709:range=limited,format=yuv420p" \
  -c:v libx264 -preset slow -crf 18 -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv \
  -c:a copy -c:s copy "output-sdr.mkv"
```

Do not use this exact chain for unknown transfer, unusual range, Dolby Vision enhancement data, or a delivery requirement that needs HDR10+/dynamic metadata. Do not carry HDR mastering/content-light metadata onto the SDR video. Preserve only compatible audio/subtitle streams and verify output tags.

## Output format

Use exactly these labels in this order:

### Source assessment
- Summarize the color metadata in 3 to 6 short bullets.
- State whether the source is PQ HDR, HLG HDR, SDR, or uncertain, and why.
- State whether mastering metadata is present.

### Recommended command
- Return one ready-to-run FFmpeg command in a fenced bash block.
- Use descriptive placeholder filenames if the real path is not provided.

### Why this command
- Explain the reasoning in 2 to 5 bullets.
- Mention transfer characteristics, tone-mapping filter choice, tag reset, and audio handling.

### Warnings
- Always warn that tone mapping is approximate and irreversible.
- Warn that the original HDR file should be kept.
- Warn that missing color metadata makes conversion unreliable.
- Warn against copying HDR tags onto SDR output.
- Warn that clipping and desaturation can occur.

## Decision defaults

Do not tone-map with missing or conflicting HDR evidence. Keep the original HDR source, test a representative sample, set output SDR tags only after pixel conversion, and verify output tags and playback.

## Practical command patterns

### Inspect HDR metadata

```bash
ffprobe -v error -select_streams v:0 \
  -show_entries stream=color_range,color_space,color_transfer,color_primaries,pix_fmt,profile \
  -of default=nw=1 input.ext
```
