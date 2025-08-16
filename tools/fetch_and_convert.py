#!/usr/bin/env python3
"""Download an image and convert to EPS using Pillow.

Usage:
    python tools/fetch_and_convert.py URL OUTPUT

The source image should be from Wikimedia Commons and carry a Public Domain or
CC BY/SA license. Metadata should be recorded in CREDITS.md.
"""
import argparse
import os
import urllib.request

try:
    from PIL import Image
except ImportError as exc:
    raise SystemExit("Pillow is required for fetch_and_convert.py" ) from exc


def fetch_and_convert(url: str, output_path: str) -> None:
    """Fetch an image from ``url`` and write an EPS file to ``output_path``."""
    tmp_path = output_path + ".download"
    urllib.request.urlretrieve(url, tmp_path)
    with Image.open(tmp_path) as img:
        rgb = img.convert("RGB")
        rgb.save(output_path, format="EPS")
    os.remove(tmp_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch image and convert to EPS")
    parser.add_argument("url", help="Image URL (Wikimedia Commons)")
    parser.add_argument("output", help="Output EPS filepath")
    args = parser.parse_args()
    fetch_and_convert(args.url, args.output)


if __name__ == "__main__":
    main()
