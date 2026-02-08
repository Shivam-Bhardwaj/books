#!/usr/bin/env python3
"""
Publish a book's public artifacts from `books/<slug>/` into `site/books/<slug>/`.

This intentionally avoids any build system: it's a deterministic file sync.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path


PUBLIC_DIRS = ("assets", "manuscript", "style", "build", "meta")
PUBLIC_FILES = ("index.html",)  # book table of contents (preferred)


def copy_tree(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst, dirs_exist_ok=True)


def copy_file(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--slug", required=True, help="Book slug, e.g. butterfly-effect")
    p.add_argument(
        "--root",
        default=".",
        help="Repo root (default: current directory)",
    )
    args = p.parse_args(argv)

    root = Path(args.root).resolve()
    slug = args.slug.strip().strip("/").replace("\\", "/")
    if not slug or "/" in slug:
        raise SystemExit(f"Invalid --slug: {args.slug!r}")

    src_root = root / "books" / slug
    dst_root = root / "site" / "books" / slug

    if not src_root.is_dir():
        print(f"Source book not found: {src_root}", file=sys.stderr)
        return 2

    # Ensure destination exists (so `site/books/` is created when missing).
    dst_root.mkdir(parents=True, exist_ok=True)

    for d in PUBLIC_DIRS:
        copy_tree(src_root / d, dst_root / d)

    for f in PUBLIC_FILES:
        copy_file(src_root / f, dst_root / f)

    # Back-compat: older books only generated `build/index.html`.
    # If no root `index.html` exists, synthesize one by rewriting relative paths.
    dst_index = dst_root / "index.html"
    if not dst_index.exists():
        build_index = dst_root / "build" / "index.html"
        if build_index.exists():
            fixed = build_index.read_text(encoding="utf-8")
            fixed = fixed.replace('href="../style/novel.css"', 'href="style/novel.css"')
            fixed = fixed.replace('href="../manuscript/', 'href="manuscript/')
            fixed = fixed.replace('src="../assets/', 'src="assets/')
            dst_index.write_text(fixed, encoding="utf-8")

    print(f"Published {slug} -> {os.path.relpath(dst_root, root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
