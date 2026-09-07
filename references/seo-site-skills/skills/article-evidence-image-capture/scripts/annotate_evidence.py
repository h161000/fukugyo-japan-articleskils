#!/usr/bin/env python3
"""Crop evidence screenshots, add thick red boxes, and save as WebP."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def parse_numbers(value: str, expected: int, label: str) -> tuple[int, ...]:
    try:
        numbers = tuple(int(part.strip()) for part in value.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{label} must contain integers: {value}") from exc
    if len(numbers) != expected:
        raise argparse.ArgumentTypeError(
            f"{label} requires {expected} comma-separated integers: {value}"
        )
    return numbers


def crop_value(value: str) -> tuple[int, int, int, int]:
    numbers = parse_numbers(value, 4, "--crop")
    if numbers[2] <= 0 or numbers[3] <= 0:
        raise argparse.ArgumentTypeError("--crop width and height must be positive")
    return numbers  # type: ignore[return-value]


def box_value(value: str) -> tuple[int, int, int, int]:
    numbers = parse_numbers(value, 4, "--box")
    if numbers[2] <= numbers[0] or numbers[3] <= numbers[1]:
        raise argparse.ArgumentTypeError("--box requires x2>x1 and y2>y1")
    return numbers  # type: ignore[return-value]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Crop a screenshot, add evidence boxes, and save a WebP image."
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--crop", type=crop_value, help="x,y,width,height")
    parser.add_argument(
        "--box",
        action="append",
        type=box_value,
        default=[],
        help="x1,y1,x2,y2 after cropping; repeat for multiple boxes",
    )
    parser.add_argument("--color", default="#e60012")
    parser.add_argument("--stroke-width", type=int, default=12)
    parser.add_argument("--quality", type=int, default=88)
    args = parser.parse_args()

    if not args.input.is_file():
        parser.error(f"input not found: {args.input}")
    if args.output.suffix.lower() != ".webp":
        parser.error("output must use the .webp extension")
    if not 1 <= args.stroke_width <= 100:
        parser.error("stroke-width must be between 1 and 100")
    if not 1 <= args.quality <= 100:
        parser.error("quality must be between 1 and 100")
    if shutil.which("magick") is None:
        parser.error("ImageMagick command 'magick' is not available")

    command = ["magick", str(args.input)]
    if args.crop:
        x, y, width, height = args.crop
        command += ["-crop", f"{width}x{height}+{x}+{y}", "+repage"]

    if args.box:
        command += [
            "-stroke",
            args.color,
            "-strokewidth",
            str(args.stroke_width),
            "-fill",
            "none",
        ]
        drawing = " ".join(
            f"rectangle {x1},{y1} {x2},{y2}" for x1, y1, x2, y2 in args.box
        )
        command += ["-draw", drawing]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    command += ["-quality", str(args.quality), str(args.output)]

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        if result.stdout:
            print(result.stdout, file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode

    identify = subprocess.run(
        ["magick", "identify", "-format", "%w x %h | %m | %b", str(args.output)],
        capture_output=True,
        text=True,
    )
    if identify.returncode != 0:
        print(identify.stderr, file=sys.stderr)
        return identify.returncode

    print(f"saved: {args.output}")
    print(identify.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
