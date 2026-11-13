# FFmpeg command patterns

Adapt these templates to the supplied stream metadata. They assume a typical 8-bit SDR source at or below 1920×1080 and a requested 1080p viewing derivative. Do not use them unchanged for HDR, high-bit-depth, unusual chroma formats, sources larger than the target, or uncertain stream layouts.

## Progressive source: practical viewing derivative

```bash
ffmpeg -i "input.ext" \
  -map 0:v:0 -map "0:a?" \
  -vf "scale=1920:1080:flags=lanczos:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1" \
  -c:v libx264 -preset slow -crf 18 -c:a copy -map_metadata 0 \
  "output-1080p.mkv"
```

Use only when resizing to 1920×1080 is requested and will not downscale an unwanted larger source. The output is a lossy H.264 derivative. Add a pixel-format option only when source details and the desired output justify it. Add only supplied color tags when the encoding path supports them.

## Clearly interlaced source: practical viewing derivative

```bash
ffmpeg -i "input.ext" \
  -map 0:v:0 -map "0:a?" \
  -vf "bwdif=mode=send_frame:parity=auto:deint=all,scale=1920:1080:flags=lanczos:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1" \
  -c:v libx264 -preset slow -crf 18 -c:a copy -map_metadata 0 \
  "output-1080p.mkv"
```

Use only when supplied field-order or `idet` evidence clearly supports deinterlacing. `send_frame` avoids doubling the output frame rate. Check for telecine or mixed content before applying this pattern.

## Lossless filtered derivative

For an explicitly requested lossless derivative, use FFV1 in MKV and choose a pixel format compatible with the source. Scaling and deinterlacing still alter the picture; retain the original as the source master. Do not assume the format from this template fits every source.

## Stream-copy reminder

When no resizing or filtering is needed, consider remuxing with stream copy instead of re-encoding. Confirm that the selected output container supports every copied stream. A remux does not improve source quality.
