#!/usr/bin/env python3
"""
Sync `books/` -> `site/books/`.

For each book:
- optionally runs `books/<slug>/build/convert.py` (if present)
- publishes public artifacts via `tools/publish_book.py`
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str], *, cwd: Path) -> None:
    p = subprocess.run(cmd, cwd=str(cwd))
    if p.returncode != 0:
        raise SystemExit(p.returncode)


def _discover_slugs(root: Path) -> list[str]:
    books_dir = root / "books"
    if not books_dir.is_dir():
        return []
    slugs: list[str] = []
    for p in sorted(books_dir.iterdir()):
        if not p.is_dir():
            continue
        if p.name.startswith("."):
            continue
        slugs.append(p.name)
    return slugs


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="Repo root (default: cwd)")
    ap.add_argument("--slug", help="Only sync a single book slug")
    ap.add_argument("--no-build", action="store_true", help="Skip running convert.py")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()

    slugs = [args.slug] if args.slug else _discover_slugs(root)
    if not slugs:
        print("No books found under ./books", file=sys.stderr)
        return 2

    for slug in slugs:
        book_dir = root / "books" / slug
        if not book_dir.is_dir():
            print(f"Missing book directory: {book_dir}", file=sys.stderr)
            return 2

        convert = book_dir / "build" / "convert.py"
        if not args.no_build and convert.is_file():
            _run([sys.executable, str(convert)], cwd=root)

        _run(
            [
                sys.executable,
                str(root / "tools" / "publish_book.py"),
                "--slug",
                slug,
                "--root",
                str(root),
            ],
            cwd=root,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

