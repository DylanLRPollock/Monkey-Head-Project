#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: validate_video_master.sh -i <input.mkv> [options]

Options:
  -i, --input FILE          Input MKV/MP4 file to validate (required)
  -r, --root DIR            Root directory for logs/output (defaults to parent
                            of a /final directory if detected, otherwise the
                            input file's directory)
  --clean-audio-index N     Audio stream index for the cleaned/default track
                            (default: 1)
  --ebur128-out FILE        File to write ebur128 output (defaults to
                            <root>/audio/clean/ebur128_cleaned.txt)
  --remux FILE              Optional remux output path (container cleanup)
  --skip-mpv                Skip mpv A/V sync spot checks
  -h, --help                Show this help

Examples:
  validate_video_master.sh -i /path/to/final/master.mkv
  validate_video_master.sh -i master.mkv --clean-audio-index 1 --remux remux.mkv
USAGE
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "WARN: Missing '$1' in PATH. Some checks will be skipped." >&2
    return 1
  fi
  return 0
}

INPUT=""
ROOT=""
CLEAN_AUDIO_INDEX=1
EBUR128_OUT=""
REMUX_OUT=""
SKIP_MPV=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    -i|--input)
      INPUT="$2"
      shift 2
      ;;
    -r|--root)
      ROOT="$2"
      shift 2
      ;;
    --clean-audio-index)
      CLEAN_AUDIO_INDEX="$2"
      shift 2
      ;;
    --ebur128-out)
      EBUR128_OUT="$2"
      shift 2
      ;;
    --remux)
      REMUX_OUT="$2"
      shift 2
      ;;
    --skip-mpv)
      SKIP_MPV=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
 done

if [[ -z "$INPUT" ]]; then
  echo "ERROR: --input is required." >&2
  usage
  exit 1
fi

if [[ ! -f "$INPUT" ]]; then
  echo "ERROR: Input not found: $INPUT" >&2
  exit 1
fi

if [[ -z "$ROOT" ]]; then
  case "$INPUT" in
    */final/*)
      ROOT="$(cd "$(dirname "$INPUT")/.." && pwd)"
      ;;
    *)
      ROOT="$(cd "$(dirname "$INPUT")" && pwd)"
      ;;
  esac
fi

if [[ -z "$EBUR128_OUT" ]]; then
  EBUR128_OUT="$ROOT/audio/clean/ebur128_cleaned.txt"
fi

echo "==> Input: $INPUT"
echo "==> Root:  $ROOT"
echo "==> Cleaned audio index: $CLEAN_AUDIO_INDEX"

if require_cmd ffprobe; then
  echo "\n==> Track layout + defaults (audio streams)"
  ffprobe -hide_banner -select_streams a \
    -show_entries stream=index,codec_name,channels,sample_rate:stream_disposition=default:stream_tags=language,title \
    -of default=nw=1 "$INPUT"
fi

if ! $SKIP_MPV; then
  if require_cmd mpv; then
    echo "\n==> A/V sync spot checks (manual review)"
    mpv "$INPUT" --aid=$((CLEAN_AUDIO_INDEX + 1)) --start=00:05:00 --length=00:02:00
    mpv "$INPUT" --aid=$((CLEAN_AUDIO_INDEX + 1)) --start=01:10:00 --length=00:02:00
    mpv "$INPUT" --aid=$((CLEAN_AUDIO_INDEX + 1)) --start=02:15:00 --length=00:02:00
  else
    echo "\n==> Skipping mpv checks (mpv not available)."
  fi
else
  echo "\n==> Skipping mpv checks (--skip-mpv)."
fi

if require_cmd ffmpeg; then
  echo "\n==> Decode scan (video)"
  ffmpeg -nostdin -hide_banner -v error \
    -i "$INPUT" -map 0:v:0 -f null -

  echo "\n==> Decode scan (cleaned audio)"
  ffmpeg -nostdin -hide_banner -v error \
    -i "$INPUT" -map 0:a:$CLEAN_AUDIO_INDEX -f null -

  echo "\n==> Loudness/peak check (ebur128)"
  mkdir -p "$(dirname "$EBUR128_OUT")"
  ffmpeg -nostdin -hide_banner \
    -i "$INPUT" -map 0:a:$CLEAN_AUDIO_INDEX \
    -af ebur128=peak=true \
    -f null - 2> "$EBUR128_OUT"
  sed -n '1,160p' "$EBUR128_OUT"
fi

if [[ -n "$REMUX_OUT" ]]; then
  if require_cmd ffmpeg; then
    echo "\n==> Remuxing with regenerated PTS"
    ffmpeg -nostdin -y -hide_banner \
      -fflags +genpts \
      -i "$INPUT" \
      -map 0 -c copy \
      "$REMUX_OUT"
    echo "Remuxed file: $REMUX_OUT"
  fi
fi

echo "\n==> Done."
