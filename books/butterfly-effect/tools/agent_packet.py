#!/usr/bin/env python3
"""
Bundle the context for running a specific agent role on a specific chapter.

This is for cases where the model does NOT have direct filesystem access.
It prints a single markdown packet to stdout that can be pasted into a chat.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

ROLE_MAP = {
    "structure": "agents/roles/structure-beat-reviewer.md",
    "continuity": "agents/roles/continuity-reviewer.md",
    "science": "agents/roles/science-reviewer.md",
    "style": "agents/roles/style-voice-reviewer.md",
    "beta": "agents/roles/beta-reader.md",
    "proof": "agents/roles/proofreader.md",
    "language": "agents/roles/language-consultant.md",
    "visual-mj": "agents/roles/visual-midjourney.md",
    "visual-runway": "agents/roles/visual-runway.md",
    "visual-inserts": "agents/roles/visual-insert-planner.md",
    "translate-hi": "agents/roles/translator-hi.md",
    "hi-naturalness": "agents/roles/hindi-naturalness-editor.md",
    "eic": "agents/roles/editor-in-chief.md",
}


CHAPTER_RE = re.compile(r'^### Chapter\s+(\d+):\s+"([^"]+)"\s*$', re.M)


def read_text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def extract_chapter_outline(chapter_num: int) -> str:
    text = read_text("outline/CHAPTERS.md")
    matches = list(CHAPTER_RE.finditer(text))
    for idx, m in enumerate(matches):
        num = int(m.group(1))
        if num != chapter_num:
            continue
        start = m.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        return text[start:end].strip()
    return ""


def parse_chapter_number(chapter_md: str) -> int | None:
    m = re.search(r"^# Chapter\s+(\d+):", chapter_md, flags=re.M)
    return int(m.group(1)) if m else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--role", required=True, choices=sorted(ROLE_MAP.keys()))
    ap.add_argument("--chapter", required=True, help="Path to .draft.md")
    ap.add_argument("--include-world", action="store_true", help="Include bible/WORLD_RULES.md")
    ap.add_argument("--include-style", action="store_true", help="Include style/STYLE_GUIDE.md")
    ap.add_argument("--include-lang", action="store_true", help="Include bible/LANGUAGES.md")
    args = ap.parse_args()

    role_path = ROLE_MAP[args.role]
    chapter_path = Path(args.chapter)
    if not chapter_path.exists():
        print(f"error: chapter not found: {chapter_path}", file=sys.stderr)
        return 2

    role_text = read_text(role_path)
    chapter_text = chapter_path.read_text(encoding="utf-8").strip()
    ch_num = parse_chapter_number(chapter_text)
    outline_text = extract_chapter_outline(ch_num) if ch_num else ""

    parts: list[str] = []
    parts.append(f"# Agent Packet: {args.role} / {chapter_path.as_posix()}")
    parts.append("")
    parts.append("## Role Prompt")
    parts.append(role_text.strip())
    parts.append("")
    if outline_text:
        parts.append("## Outline Excerpt (Contract)")
        parts.append(outline_text)
        parts.append("")
    if args.include_style:
        parts.append("## Style Guide")
        parts.append(read_text("style/STYLE_GUIDE.md").strip())
        parts.append("")
    if args.include_world:
        parts.append("## World Rules (Canon)")
        parts.append(read_text("bible/WORLD_RULES.md").strip())
        parts.append("")
    if args.include_lang:
        parts.append("## Languages (Canon)")
        parts.append(read_text("bible/LANGUAGES.md").strip())
        parts.append("")
    parts.append("## Chapter Draft")
    parts.append(chapter_text)

    sys.stdout.write("\n".join(parts).rstrip() + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
