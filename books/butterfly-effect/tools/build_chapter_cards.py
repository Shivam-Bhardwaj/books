#!/usr/bin/env python3
"""
Generate schema/chapter-cards.yaml from outline + chapter theme list.

Inputs:
  - outline/CHAPTERS.md
  - style/chapter-svg-themes.yaml
Output:
  - schema/chapter-cards.yaml
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CHAPTERS_MD = ROOT / "outline/CHAPTERS.md"
THEMES_YAML = ROOT / "style/chapter-svg-themes.yaml"
OUT_YAML = ROOT / "schema/chapter-cards.yaml"


CHAPTER_RE = re.compile(r'^### Chapter\s+(\d+):\s+"([^"]+)"\s*$', re.M)
POV_RE = re.compile(r"^\*\*POV:\*\*\s*(.+?)\s*·\s*\*\*Location:\*\*\s*(.+?)\s*·\s*\*\*Timeline:\*\*\s*(.+?)\s*$", re.M)
WORDCOUNT_RE = re.compile(r"^\*\*Word count:\*\*\s*([0-9,]+)\s*$", re.M)
BEAT_RE = re.compile(r"^\*\*Beat\s+(\d+)\s+—\s+(.+?)\.\*\*\s*(.*)$", re.M)
HOOK_RE = re.compile(r"^\*\*CHAPTER HOOK.*?:\*\*\s*(.+)$", re.M)
CAUSAL_RE = re.compile(r"^\*\*Causal links:\*\*\s*(.+)$", re.M)


def load_theme_by_chapter() -> dict[int, dict]:
    data = yaml.safe_load(THEMES_YAML.read_text(encoding="utf-8"))
    out: dict[int, dict] = {}
    for ch in data.get("chapters", []):
        out[int(ch["chapter"])] = ch
    return out


def world_from_pov(pov: str) -> str:
    p = pov.lower()
    if "sūrya" in p or "surya" in p:
        return "antarctic"
    if "kael" in p or "moss" in p:
        return "continental"
    return "dual"


def register_hint(world: str) -> str:
    if world == "continental":
        return "earthy, bodily, jagged sentences, glass/sea metaphors"
    if world == "antarctic":
        return "clean cadence, precise diction, geometry/light metaphors"
    return "contrast: warm grit vs clean geometry; show translation loss"


def parse_chapters(text: str) -> list[dict]:
    themes = load_theme_by_chapter()
    matches = list(CHAPTER_RE.finditer(text))
    chapters: list[dict] = []

    for idx, m in enumerate(matches):
        num = int(m.group(1))
        title = m.group(2).strip()
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        block = text[start:end]

        pov = location = timeline = "Unknown"
        pov_m = POV_RE.search(block)
        if pov_m:
            pov = pov_m.group(1).strip()
            location = pov_m.group(2).strip()
            timeline = pov_m.group(3).strip()

        wc_m = WORDCOUNT_RE.search(block)
        word_count = wc_m.group(1).replace(",", "") if wc_m else ""

        beats = []
        for bm in BEAT_RE.finditer(block):
            beat_num = int(bm.group(1))
            beat_title = bm.group(2).strip()
            beat_desc = bm.group(3).strip()
            beats.append({"beat": beat_num, "title": beat_title, "desc": beat_desc})

        hook_m = HOOK_RE.search(block)
        hook = hook_m.group(1).strip() if hook_m else ""

        causal_m = CAUSAL_RE.search(block)
        causal = causal_m.group(1).strip() if causal_m else ""

        theme = themes.get(num, {})
        world = world_from_pov(pov)

        chapters.append(
            {
                "chapter": num,
                "title": title,
                "pov": pov,
                "world": world,
                "register_hint": register_hint(world),
                "location": location,
                "timeline": timeline,
                "word_count_target": word_count,
                "beats": beats,
                "hook": hook,
                "causal_links": causal,
                "theme_keywords": theme.get("theme_keywords", []),
                "motif": theme.get("motif", ""),
                "svg_prompt": theme.get("svg_prompt", ""),
            }
        )

    chapters.sort(key=lambda x: x["chapter"])
    return chapters


def main() -> None:
    text = CHAPTERS_MD.read_text(encoding="utf-8")
    cards = parse_chapters(text)
    OUT_YAML.parent.mkdir(parents=True, exist_ok=True)
    out = {
        "meta": {
            "generated_from": [str(CHAPTERS_MD.relative_to(ROOT)), str(THEMES_YAML.relative_to(ROOT))],
            "note": "Chapter cards for agent context and translation/visual consistency.",
        },
        "chapters": cards,
    }
    OUT_YAML.write_text(yaml.safe_dump(out, sort_keys=False, allow_unicode=False), encoding="utf-8")
    print(f"Wrote {OUT_YAML.relative_to(ROOT)} ({len(cards)} chapters)")


if __name__ == "__main__":
    main()

