#!/usr/bin/env python3
"""
Generate baseline Midjourney + Runway prompts per chapter.

Source of truth for chapters: outline/CHAPTERS.md
Theme motifs: style/chapter-svg-themes.yaml
Output: agents/visual/chapter-visual-prompts.yaml
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml


CHAPTERS_MD = Path("outline/CHAPTERS.md")
THEMES_YAML = Path("style/chapter-svg-themes.yaml")
OUT_YAML = Path("agents/visual/chapter-visual-prompts.yaml")


CHAPTER_RE = re.compile(r'^### Chapter\s+(\d+):\s+"([^"]+)"\s*$', re.M)


def parse_chapters_md(text: str) -> list[dict]:
    chapters: list[dict] = []
    matches = list(CHAPTER_RE.finditer(text))
    for idx, m in enumerate(matches):
        num = int(m.group(1))
        title = m.group(2).strip()
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        block = text[start:end]

        pov_m = re.search(r"^\*\*POV:\*\*\s*(.+?)\s*·", block, re.M)
        pov = (pov_m.group(1).strip() if pov_m else "Unknown").strip()

        hook_m = re.search(r"^\*\*CHAPTER HOOK.*?:\*\*\s*(.+)$", block, re.M)
        hook = (hook_m.group(1).strip() if hook_m else "").strip()

        chapters.append({"chapter": num, "title": title, "pov": pov, "hook": hook})
    chapters.sort(key=lambda x: x["chapter"])
    return chapters


def load_theme_by_chapter() -> dict[int, dict]:
    data = yaml.safe_load(THEMES_YAML.read_text(encoding="utf-8"))
    out: dict[int, dict] = {}
    for ch in data.get("chapters", []):
        out[int(ch["chapter"])] = ch
    return out


def world_tags(pov: str) -> tuple[str, str]:
    p = pov.lower()
    if "sūrya" in p or "surya" in p:
        return (
            "Antarctic sealed habitat, clean geometry, diffuse light, minimalism, mesh-era hard sci-fi",
            "slow, stable camera, centered composition, quiet precision",
        )
    if "kael" in p or "moss" in p:
        return (
            "post-collapse coastal city-state, hand-made tools, weathered ruins, dust motes, salt air, hard sci-fi realism",
            "cinematic 35mm look, tactile texture, shallow depth of field",
        )
    return (
        "two worlds colliding, warm grit against cold geometry, translation distortion motif, hard sci-fi realism",
        "balanced composition with deliberate misalignment (refraction/offset)",
    )


def character_tags(pov: str) -> str:
    p = pov.lower()
    if "kael" in p:
        return "Kael: dark brown skin, close-cropped hair, burn scar on left forearm, strong hands"
    if "moss" in p:
        return "Moss: weathered sailor build, crooked/broken nose, tar-and-salt texture"
    if "sūrya" in p or "surya" in p:
        return "Sūrya: very pale skin, large gray eyes, long dark hair, precise posture"
    if "dual" in p:
        return "Dual POV: contrast between Continental warmth and Antarctic precision"
    return "Characters: keep features consistent with the character bible"


def build_prompts(ch: dict, theme: dict) -> dict:
    vibe, camera = world_tags(ch["pov"])
    chars = character_tags(ch["pov"])
    motif = theme.get("motif", "")
    keywords = theme.get("theme_keywords", [])

    # Keep prompts short and reusable; deeper specificity belongs in a human/agent pass.
    cover = (
        f"{ch['title']}, theme: {', '.join(keywords)}. "
        f"Visual motif: {motif}. "
        f"{chars}. {vibe}. {camera}. "
        "editorial hard sci-fi, high detail, restrained color, no text"
    )
    scene = (
        f"Key moment from '{ch['title']}': {ch['hook']} "
        f"{chars}. {vibe}. {camera}. "
        "no text"
    ).strip()

    mj_params = "--ar 16:9 --style raw --stylize 100 --no text --no letters --no watermark --no logo"
    runway = (
        f"Atmospheric cinematic shot inspired by '{ch['title']}': {motif}. "
        f"{vibe}. {camera}. No text."
    )

    neg = "text, subtitles, watermark, logo, UI overlay, low-res, blurry faces"

    return {
        "chapter": ch["chapter"],
        "title": ch["title"],
        "pov": ch["pov"],
        "theme_keywords": keywords,
        "motif": motif,
        "mj": {
            "cover_still_prompt": cover,
            "scene_still_prompt": scene,
            "params": mj_params,
            "negative": "--no text --no letters --no watermark --no logo --no subtitles",
        },
        "runway": {
            "video_prompt": runway,
            "camera": camera,
            "negative": neg,
            "aspect": "16:9",
            "duration_s": "4-8",
        },
    }


def main() -> None:
    chapters = parse_chapters_md(CHAPTERS_MD.read_text(encoding="utf-8"))
    themes = load_theme_by_chapter()

    items = []
    for ch in chapters:
        theme = themes.get(ch["chapter"], {})
        items.append(build_prompts(ch, theme))

    out = {
        "meta": {
            "generated_from": [str(CHAPTERS_MD), str(THEMES_YAML)],
            "aspect_ratio_default": "16:9",
            "note": "Baseline prompts; refine per chapter with character/scene specificity as needed.",
        },
        "chapters": items,
    }

    OUT_YAML.parent.mkdir(parents=True, exist_ok=True)
    OUT_YAML.write_text(yaml.safe_dump(out, sort_keys=False, allow_unicode=False), encoding="utf-8")
    print(f"Wrote {OUT_YAML} ({len(items)} chapters)")


if __name__ == "__main__":
    main()
