#!/usr/bin/env python3
"""Convert raw Midjourney illustration PNGs/JPGs to optimized WebP + AVIF at multiple widths.

Usage:
    python3 tools/optimize_illustrations.py               # all images
    python3 tools/optimize_illustrations.py --chapter 1    # only ch01-*
    python3 tools/optimize_illustrations.py --force        # overwrite existing
"""

import argparse
import os
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required: pip install Pillow")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE, "assets", "illustrations", "raw")
OUT_DIR = os.path.join(BASE, "assets", "illustrations")

WIDTHS = [480, 768, 1200]
WEBP_QUALITY = 82
AVIF_QUALITY = 60


def optimize_image(src_path, force=False):
    """Generate WebP (and optionally AVIF) variants at each target width."""
    basename = os.path.splitext(os.path.basename(src_path))[0]  # e.g. ch01-sealed-room

    try:
        img = Image.open(src_path)
    except Exception as e:
        print(f"  ! Could not open {src_path}: {e}")
        return 0

    img = img.convert("RGB")
    orig_w, orig_h = img.size
    count = 0

    for w in WIDTHS:
        if w > orig_w:
            target_w = orig_w
        else:
            target_w = w
        ratio = target_w / orig_w
        target_h = int(orig_h * ratio)
        resized = img.resize((target_w, target_h), Image.LANCZOS)

        # WebP
        webp_path = os.path.join(OUT_DIR, f"{basename}-{w}w.webp")
        if force or not os.path.exists(webp_path):
            resized.save(webp_path, "WEBP", quality=WEBP_QUALITY, method=6)
            print(f"  + {os.path.basename(webp_path)}")
            count += 1

        # AVIF (requires pillow-avif-plugin or Pillow >= 10.1)
        avif_path = os.path.join(OUT_DIR, f"{basename}-{w}w.avif")
        if force or not os.path.exists(avif_path):
            try:
                resized.save(avif_path, "AVIF", quality=AVIF_QUALITY)
                print(f"  + {os.path.basename(avif_path)}")
                count += 1
            except Exception:
                pass  # AVIF not available; WebP is sufficient

    return count


def main():
    parser = argparse.ArgumentParser(description="Optimize illustration images")
    parser.add_argument("--chapter", type=int, help="Only process images for this chapter number")
    parser.add_argument("--force", action="store_true", help="Overwrite existing optimized files")
    args = parser.parse_args()

    if not os.path.isdir(RAW_DIR):
        os.makedirs(RAW_DIR, exist_ok=True)
        print(f"Created {RAW_DIR} — drop raw MJ images here.")
        return

    # Collect source images
    sources = []
    for fname in sorted(os.listdir(RAW_DIR)):
        if not fname.lower().endswith((".png", ".jpg", ".jpeg")):
            continue
        if args.chapter is not None:
            prefix = f"ch{args.chapter:02d}-"
            if not fname.startswith(prefix):
                continue
        sources.append(os.path.join(RAW_DIR, fname))

    if not sources:
        chap_note = f" for chapter {args.chapter}" if args.chapter else ""
        print(f"No raw images found{chap_note} in {RAW_DIR}")
        return

    os.makedirs(OUT_DIR, exist_ok=True)
    total = 0
    for src in sources:
        print(f"Processing {os.path.basename(src)}...")
        total += optimize_image(src, force=args.force)

    print(f"\nDone. {total} files written to {OUT_DIR}")


if __name__ == "__main__":
    main()
