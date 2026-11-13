---
name: ffmpeg-video-upscale
description: Analyze user-provided FFmpeg or ffprobe metadata and recommend a conservative 1080p viewing derivative. Use when deciding whether to deinterlace, how to preserve aspect ratio, whether to crop, and how to handle video, audio, container, frame rate, and known color metadata. Return one ready-to-run Linux command with source-specific choices and clear limitations.
---

# FFmpeg Video Upscale

## Purpose

Turn supplied media metadata into one conservative, source-aware FFmpeg command for a 1080p viewing derivative. Protect the source: never imply an upscale restores detail or that a filtered derivative replaces the original. Base decisions only on information the user supplied. Do not claim to have inspected or processed media.

If the user asks for a different output size, optimize for that request. If the goal or essential stream details are unclear, state the uncertainty and ask only for the missing information that would change the recommendation.

## Workflow

1. Read all supplied `ffprobe`, `idet`, `cropdetect`, and `mediainfo` output.
2. Identify the relevant video and audio streams. Note container, codecs, dimensions, display and sample aspect ratios, frame rate, field order/interlace evidence, pixel format and bit depth, color metadata, and any crop evidence.
3. Classify scan type as **progressive**, **interlaced**, or **uncertain**. Use field-order data or clear `idet` results; codec name alone is not proof.
4. Decide whether a 1920×1080 output would upscale, preserve size, or downscale the source. Do not shrink a higher-resolution source unless the requested target calls for it.
5. Choose the least invasive path supported by the evidence. Give one command, a short rationale, and only applicable warnings.

## Source and framing rules

- A scale filter can enlarge pixels; it cannot recover detail absent from the source.
- Never stretch. Preserve the display aspect ratio. For a requested 1920×1080 frame, scale to fit and pad the remaining space; make output pixels square with `setsar=1` when appropriate.
- If the source already exceeds the requested dimensions and the user has not asked for downscaling, do not force it to 1920×1080. Recommend a size-preserving cleanup or ask which target they want.
- Do not crop by default. Treat cropdetect as a suggestion, not proof of removable borders. Recommend a crop only when the user requests it and the evidence is credible; say visual confirmation is needed.
- Do not change frame rate or interpolate frames by default.

## Interlace rules

- Do not deinterlace progressive material.
- When metadata is incomplete or conflicting, call scan type uncertain and leave deinterlacing out.
- Recommend deinterlacing only when field-order data or clear `idet` evidence supports it. Use a standard filter such as `bwdif`, with `mode=send_frame` to avoid doubling the frame rate. Put deinterlacing before scaling.
- Do not mistake telecine or mixed content for ordinary interlace; explain the uncertainty and request more evidence when it changes the command.

## Container and stream handling

- Use MKV for a newly encoded derivative when the input container is not MKV, or when MKV is otherwise the practical target. If the input is already MKV, keep it.
- Map the primary video stream and available audio streams explicitly. Include subtitles only when their presence and compatibility are known or the user asks to keep them.
- Copy audio when the codec is supported by the output container and no audio change is needed. Do not resample, remix, normalize, or transcode it by default.
- Converting lossy audio to FLAC does not restore lost quality and can increase file size. Use FLAC only if the user explicitly wants a lossless encoding of the decoded audio or the source audio itself is lossless and conversion is justified.
- If audio must be transcoded for compatibility, choose a suitable target codec and explain that it is a lossy or format-changing step.

## Video quality and pixel format

- For a practical viewing derivative, use `libx264` with a high-quality CRF setting (usually 18–20) and a slower preset when compatible. Explain that this is a lossy encode.
- Do not call an ordinary CRF encode lossless.
- For a user-requested lossless filtered derivative, use FFV1 in MKV where supported. Filtering or scaling still changes the picture, so the original remains the source master.
- Use x264 lossless only when explicitly requested and compatible with the source format and intended playback. Do not silently convert high-bit-depth or non-4:2:0 video to 8-bit 4:2:0.
- Choose an output pixel format from supplied source details and encoder support. If bit depth, chroma format, or color handling matters but is unknown, state that limitation instead of guessing.
- Do not recommend AI upscaling, sharpening, denoising, color manipulation, or frame interpolation unless requested or clearly justified.

## Color metadata

- Preserve source color metadata when it is supplied and the output path supports it.
- Pass only known values, such as primaries, transfer characteristics, matrix/colorspace, or range. Never invent tags.
- If HDR metadata is present, do not silently convert to SDR or discard HDR signaling. Explain that an HDR-aware workflow is needed if the chosen encoder or command would not preserve it.

## Command construction

For a typical 8-bit SDR source at or below 1080p, use the reference patterns in `references/command-patterns.md`. Adapt stream selection, filter chain, codecs, pixel format, frame size, and known color options to the supplied metadata. Use descriptive placeholder filenames when paths are absent. Do not include speculative flags.

If the user has not provided enough information to safely choose a command, keep the required response headings and state what metadata is missing under Warnings rather than fabricating source properties.

## Response format

Use these headings in this order:

### Source assessment
- Give 3–6 concise bullets summarizing the relevant supplied facts.
- State progressive, interlaced, or uncertain and the evidence.
- State whether crop evidence is trustworthy, weak, or absent.
- Say whether 1080p would upscale, preserve size, or downscale the source.

### Recommended command
- Give one ready-to-run command in a fenced `bash` block.
- Use descriptive placeholder filenames if the user gave no paths.
- Do not present alternatives unless the user asks to compare them.

### Why this command
- Explain the chosen scaling/framing, scan handling, codec, container, audio handling, frame rate, and color treatment that apply.

### Warnings
- Always warn against stretching.
- Warn against blind cropping when evidence is weak or absent.
- Warn against deinterlacing when scan type is progressive or uncertain.
- Include other warnings only when they apply, including lossy encoding, HDR handling, pixel-format conversion, or missing metadata.
