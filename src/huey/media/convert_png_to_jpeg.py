"""Convert PNG images to JPEG format."""

from __future__ import annotations

import argparse
from pathlib import Path


def convert_png_to_jpeg(
    png_file: str | Path,
    output_file: str | Path,
    quality: int = 85,
) -> Path:
    """Convert a PNG image to JPEG."""

    source = Path(png_file).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"PNG file '{source}' not found.")

    target = Path(output_file).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    from PIL import Image

    with Image.open(source) as image:
        if image.mode in {"RGBA", "LA"}:
            background = Image.new("RGB", image.size, (255, 255, 255))
            background.paste(image, mask=image.getchannel("A"))
            image = background
        else:
            image = image.convert("RGB")
        image.save(target, "JPEG", quality=quality)
    return target


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""

    parser = argparse.ArgumentParser(description="Convert a PNG image to JPEG.")
    parser.add_argument("png_file", help="Path to the input PNG file.")
    parser.add_argument("output_file", help="Path to the output JPEG file.")
    parser.add_argument(
        "--quality",
        type=int,
        default=85,
        help="JPEG quality from 1 (worst) to 95 (best).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""

    args = build_parser().parse_args(argv)
    convert_png_to_jpeg(args.png_file, args.output_file, args.quality)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
