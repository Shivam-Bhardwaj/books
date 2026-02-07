#!/usr/bin/env python3
"""
Lightweight prose lint for The Sundering drafts.

Focus: STYLE_GUIDE forbidden phrases + a few POV-dependent checks.
This is not a grammar checker; it's a friction detector.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    kind: str
    message: str
    excerpt: str


FORBIDDEN_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    ("forbidden", re.compile(r"\bsuddenly\b", re.IGNORECASE), 'Banned: "suddenly"'),
    ("forbidden", re.compile(r"\bvery\b", re.IGNORECASE), 'Banned: "very"'),
    ("forbidden", re.compile(r"\breally\b", re.IGNORECASE), 'Banned: "really"'),
    ("forbidden", re.compile(r"\bbegan to\b", re.IGNORECASE), 'Banned: "began to"'),
    ("forbidden", re.compile(r"\bstarted to\b", re.IGNORECASE), 'Banned: "started to"'),
    ("forbidden", re.compile(r"\bseemed to\b", re.IGNORECASE), 'Banned: "seemed to"'),
    ("forbidden", re.compile(r"\bappeared to\b", re.IGNORECASE), 'Banned: "appeared to"'),
    ("forbidden", re.compile(r"a chill ran down", re.IGNORECASE), "Banned cliche: chill/spine"),
    ("forbidden", re.compile(r"let out a breath", re.IGNORECASE), "Banned cliche: breath (didn't know holding)"),
    ("forbidden", re.compile(r"\borbs\b", re.IGNORECASE), 'Banned: "orbs"'),
    ("forbidden", re.compile(r"\bsmirked\b", re.IGNORECASE), 'Banned dialogue tag: "smirked"'),
]


META_RE = re.compile(
    r"<!--\s*Arc:\s*(\d+)\s*\|\s*POV:\s*(.+?)\s*\|\s*Location:\s*(.+?)\s*\|\s*Timeline:\s*(.+?)\s*-->",
    re.IGNORECASE,
)

TITLE_RE = re.compile(r"^# Chapter\s+(\d+):\s*(.+)$")


def is_continental_pov(pov: str) -> bool:
    # Heuristic based on existing bible: Kael/Moss are Continental POV; Sūrya is Antarctic.
    p = pov.lower()
    if "sūrya" in p or "surya" in p:
        return False
    if "kael" in p or "moss" in p:
        return True
    # "Dual" chapters: treat as mixed; don't enforce semicolon rule.
    if "dual" in p or "+" in p:
        return False
    return False


def lint_file(path: Path) -> tuple[dict[str, str], list[Finding]]:
    txt = path.read_text(encoding="utf-8")
    lines = txt.splitlines()

    meta: dict[str, str] = {"chapter": "?", "title": "?", "arc": "?", "pov": "?", "location": "?", "timeline": "?"}

    for i, line in enumerate(lines, start=1):
        m = TITLE_RE.match(line.strip())
        if m:
            meta["chapter"] = m.group(1)
            meta["title"] = m.group(2).strip()
            break

    for line in lines[:40]:
        m = META_RE.search(line)
        if m:
            meta["arc"] = m.group(1).strip()
            meta["pov"] = m.group(2).strip()
            meta["location"] = m.group(3).strip()
            meta["timeline"] = m.group(4).strip()
            break

    findings: list[Finding] = []

    whispered = 0
    exclamations = 0
    semicolons = 0

    for i, line in enumerate(lines, start=1):
        s = line
        # Ignore HTML comment lines used for beats/metadata.
        if "<!--" in s:
            continue

        if "whispered" in s.lower():
            whispered += len(re.findall(r"\bwhispered\b", s, flags=re.IGNORECASE))
        exclamations += s.count("!")
        semicolons += s.count(";")

        for kind, pat, msg in FORBIDDEN_PATTERNS:
            if pat.search(s):
                excerpt = s.strip()
                if len(excerpt) > 160:
                    excerpt = excerpt[:157] + "..."
                findings.append(
                    Finding(
                        path=str(path),
                        line=i,
                        kind=kind,
                        message=msg,
                        excerpt=excerpt,
                    )
                )

    if whispered > 2:
        findings.append(
            Finding(
                path=str(path),
                line=0,
                kind="style",
                message=f'Overuse: "whispered" occurs {whispered}x (style guide: <= 2x/chapter).',
                excerpt="",
            )
        )

    if exclamations >= 6:
        findings.append(
            Finding(
                path=str(path),
                line=0,
                kind="style",
                message=f"High exclamation count: {exclamations} occurrences. Consider reducing narration exclamation marks.",
                excerpt="",
            )
        )

    if meta.get("pov", "?") != "?" and is_continental_pov(meta["pov"]) and semicolons > 0:
        findings.append(
            Finding(
                path=str(path),
                line=0,
                kind="style",
                message=f"Continental POV semicolons: {semicolons} occurrences (STYLE_GUIDE: avoid semicolons in Continental chapters).",
                excerpt="",
            )
        )

    return meta, findings


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+", help="Draft markdown files (.draft.md)")
    args = ap.parse_args()

    all_findings: list[Finding] = []
    for p in args.paths:
        path = Path(p)
        if not path.exists():
            print(f"error: not found: {p}", file=sys.stderr)
            return 2
        meta, findings = lint_file(path)
        words = len(re.findall(r"\b\\w+\\b", path.read_text(encoding="utf-8")))

        print(f"\n{path}")
        print(f"  Chapter: {meta['chapter']}  Title: {meta['title']}")
        print(f"  Arc: {meta['arc']}  POV: {meta['pov']}")
        print(f"  Words: {words}")

        if not findings:
            print("  Findings: none")
        else:
            print(f"  Findings: {len(findings)}")
            for f in findings:
                loc = f"L{f.line}" if f.line else "-"
                if f.excerpt:
                    print(f"    [{f.kind}] {loc}: {f.message} :: {f.excerpt}")
                else:
                    print(f"    [{f.kind}] {loc}: {f.message}")
        all_findings.extend(findings)

    return 0 if not all_findings else 1


if __name__ == "__main__":
    raise SystemExit(main())

