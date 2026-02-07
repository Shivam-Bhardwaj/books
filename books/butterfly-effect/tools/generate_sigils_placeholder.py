#!/usr/bin/env python3
"""
Generate lightweight placeholder chapter sigils (SVG) from `style/chapter-svg-themes.yaml`.

These are intentionally simple: they make the reader UI work end-to-end now,
and can later be replaced 1:1 by a dedicated art agent (same filenames/ids).
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
THEMES = ROOT / "style/chapter-svg-themes.yaml"
OUT_DIR = ROOT / "assets/sigils"


@dataclass(frozen=True)
class Theme:
    id: str
    chapter: int
    title: str
    pov: str
    alt: str
    svg_prompt: str


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def svg_wrap(*, title: str, body: str, view_box: str = "0 0 256 256", stroke_width: int = 12) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view_box}" '
        f'fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" '
        f'stroke-width="{stroke_width}">'
        f"<title>{esc(title)}</title>"
        f"{body}"
        f"</svg>\n"
    )


def circle(cx: float, cy: float, r: float) -> str:
    return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}"/>'


def line(x1: float, y1: float, x2: float, y2: float) -> str:
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>'


def path(d: str) -> str:
    return f'<path d="{d}"/>'


def dots_ring(cx: float, cy: float, r: float, n: int, *, gap_index: int | None = None, dot_r: float = 4.8) -> str:
    out: list[str] = []
    for i in range(n):
        if gap_index is not None and i == gap_index:
            continue
        a = (i / n) * math.tau - math.pi / 2
        out.append(circle(cx + r * math.cos(a), cy + r * math.sin(a), dot_r))
    return "".join(out)


def template_generic(seed: int, *, geometric: bool) -> str:
    cx, cy = 128, 128
    r = 84
    # A broken circle (translation-loss motif) with a small off-axis mark.
    body = []
    body.append(path(f"M {cx-r} {cy} A {r} {r} 0 1 1 {cx+r} {cy}"))
    body.append(path(f"M {cx-r} {cy} A {r} {r} 0 0 0 {cx+r-18} {cy-48}"))

    # Add 3 nodes.
    gap = (seed % 11) + 1
    body.append(dots_ring(cx, cy, 62, 12, gap_index=gap, dot_r=4.2 if geometric else 4.8))

    # Accent stroke
    if geometric:
        body.append(line(92, 164, 164, 92))
    else:
        body.append(path("M 92 168 C 112 148, 144 148, 164 128"))

    return "".join(body)


def template_lens() -> str:
    body = []
    body.append(circle(128, 128, 84))
    body.append(circle(128, 128, 62))
    body.append(line(188, 78, 206, 66))  # scratch
    body.append(circle(96, 156, 4.6))
    body.append(circle(110, 170, 3.8))
    body.append(circle(86, 174, 3.6))
    body.append(path("M 86 128 C 104 116, 120 116, 140 128 S 172 140, 190 128"))
    return "".join(body)


def template_grid() -> str:
    body = []
    start_x, start_y = 56, 56
    size, gap = 28, 10
    for r in range(4):
        for c in range(4):
            x = start_x + c * (size + gap)
            y = start_y + r * (size + gap)
            # Shift one cell.
            if r == 2 and c == 2:
                x += 8
                y -= 6
            body.append(f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="4" ry="4"/>')
    body.append(circle(56, 56, 4.8))
    return "".join(body)


def template_dish() -> str:
    body = []
    body.append(path("M 74 170 Q 128 96 182 170"))
    body.append(line(98, 180, 158, 180))
    body.append(path("M 52 108 Q 74 98 92 82"))
    body.append(path("M 44 132 Q 68 118 86 100"))
    body.append(path("M 58 152 Q 78 140 92 124"))
    body.append(circle(44, 132, 4.6))
    return "".join(body)


def template_ring12() -> str:
    body = []
    body.append(dots_ring(128, 128, 78, 12, gap_index=2, dot_r=4.8))
    body.append(path("M 184 94 L 204 74"))
    body.append(path("M 204 74 L 208 96"))
    return "".join(body)


def template_spectacles() -> str:
    body = []
    body.append(circle(92, 132, 34))
    body.append(circle(164, 132, 34))
    body.append(line(126, 132, 130, 132))
    body.append(path("M 72 132 C 78 126, 86 126, 92 132 S 106 138, 112 132"))
    body.append(circle(164, 132, 4.8))
    return "".join(body)


def template_compass() -> str:
    body = []
    body.append(circle(128, 128, 86))
    body.append(line(128, 68, 128, 188))
    body.append(path("M 128 128 L 154 160"))
    body.append(path("M 128 128 L 102 98"))
    return "".join(body)


def template_ship() -> str:
    body = []
    body.append(path("M 58 176 H 198"))  # sea line
    body.append(path("M 104 172 L 152 172 L 142 194 H 114 Z"))  # hull
    body.append(line(128, 102, 128, 172))  # mast
    body.append(path("M 128 112 L 154 146 L 128 146 Z"))  # sail
    return "".join(body)


def template_eye(geometric: bool) -> str:
    body = []
    body.append(path("M 52 128 C 78 88, 178 88, 204 128 C 178 168, 78 168, 52 128 Z"))
    body.append(circle(128, 128, 18))
    if geometric:
        body.append(line(128, 92, 128, 164))
        body.append(path("M 128 128 L 176 108 L 176 148 Z"))
    return "".join(body)


def template_thermometer_ring() -> str:
    body = []
    body.append(dots_ring(128, 128, 78, 12, gap_index=None, dot_r=4.6))
    body.append(circle(128, 168, 10))
    body.append(line(128, 98, 128, 160))
    body.append(path("M 120 98 H 136"))
    return "".join(body)


def template_network() -> str:
    body = []
    pts = [(92, 92), (164, 92), (92, 164), (164, 164), (128, 128), (196, 140)]
    for x, y in pts:
        body.append(circle(x, y, 4.6))
    # connect but skip one link to show "missing"
    body.append(line(92, 92, 128, 128))
    body.append(line(164, 92, 128, 128))
    body.append(line(92, 164, 128, 128))
    body.append(line(164, 164, 128, 128))
    # missing link between (164,164) and (196,140)
    body.append(line(164, 92, 196, 140))
    body.append(path("M 176 132 C 184 124, 196 124, 204 132"))  # tiny question-curve-ish
    return "".join(body)


def template_helix() -> str:
    body = []
    body.append(path("M 92 64 C 148 64, 108 128, 164 128 C 220 128, 180 192, 92 192"))
    body.append(path("M 164 64 C 108 64, 148 128, 92 128 C 36 128, 76 192, 164 192"))
    body.append(line(104, 92, 152, 92))
    body.append(line(104, 164, 152, 164))
    return "".join(body)


def template_aurora() -> str:
    body = []
    body.append(path("M 52 176 H 204"))
    body.append(path("M 72 80 C 92 120, 112 120, 132 80"))
    body.append(path("M 112 76 C 132 120, 152 120, 172 76"))
    body.append(path("M 92 96 C 112 132, 144 132, 164 96"))
    body.append(circle(96, 196, 4.2))
    body.append(circle(120, 196, 4.2))
    return "".join(body)


def choose_template(t: Theme) -> str:
    p = (t.svg_prompt or "").lower()
    motif = p
    pov = (t.pov or "").lower()
    geometric = "sūrya" in pov or "antarctic" in pov

    if "lens" in motif:
        return template_lens()
    if "grid" in motif:
        return template_grid()
    if "dish" in motif:
        return template_dish()
    if "12" in motif or "twelve" in motif or "ring" in motif and "dot" in motif:
        return template_ring12()
    if "spectacles" in motif:
        return template_spectacles()
    if "compass" in motif:
        return template_compass()
    if "ship" in motif:
        return template_ship()
    if "thermometer" in motif:
        return template_thermometer_ring()
    if "network" in motif or "node" in motif:
        return template_network()
    if "helix" in motif or "dna" in motif:
        return template_helix()
    if "aurora" in motif:
        return template_aurora()
    if "eye" in motif:
        return template_eye(geometric=geometric)

    # Fallback: generic sigil with mild POV-dependent variation.
    seed = sum(ord(c) for c in t.id) % 997
    return template_generic(seed, geometric=geometric)


def main() -> int:
    cfg = load_yaml(THEMES)
    chapters = cfg.get("chapters", []) or []
    view_box = str((cfg.get("meta", {}) or {}).get("viewBox", "0 0 256 256"))
    stroke_width = int(((cfg.get("meta", {}) or {}).get("svg_style_defaults", {}) or {}).get("stroke_width", 12))

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    themes: list[Theme] = []
    for ch in chapters:
        if not isinstance(ch, dict):
            continue
        themes.append(
            Theme(
                id=str(ch["id"]),
                chapter=int(ch["chapter"]),
                title=str(ch.get("title", "")),
                pov=str(ch.get("pov", "")),
                alt=str(ch.get("alt", "")),
                svg_prompt=str(ch.get("svg_prompt", "")),
            )
        )

    # Emit placeholder sigils.
    for t in themes:
        body = choose_template(t)
        title = t.alt or f"Chapter {t.chapter}: {t.title}"
        svg = svg_wrap(title=title, body=body, view_box=view_box, stroke_width=stroke_width)
        out = OUT_DIR / f"{t.id}.svg"
        out.write_text(svg, encoding="utf-8")

    # Also emit an index for quick browsing.
    index_lines = ["# Sigils", ""]
    for t in themes:
        index_lines.append(f"- Chapter {t.chapter:02d}: `{t.id}.svg` — {t.title}")
    (OUT_DIR / "INDEX.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")

    print(f"Wrote {len(themes)} sigils to {OUT_DIR.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

