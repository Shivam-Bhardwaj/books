#!/usr/bin/env python3
"""
Translation QC checks (format + token preservation).

This does not attempt to judge literary quality. It tries to catch "hard failures":
- protected tokens got translated or dropped
- paragraph/scene-break structure drift
- leftover placeholders
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
PIPELINE_CFG = ROOT / "agents/translation/translation-pipeline.yaml"
ENTITIES_PATH = ROOT / "schema/entities.yaml"

TITLE_RE = re.compile(r"^# Chapter\s+(\d+):\s*(.+)$", re.MULTILINE)


@dataclass(frozen=True)
class QCResult:
    ok: bool
    issues: list[str]
    stats: dict[str, Any]


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def extract_prose_from_draft(md: str) -> str:
    lines = md.splitlines()
    prose_lines: list[str] = []
    in_comment_block = False
    for line in lines:
        if re.match(r"^# Chapter \d+:", line):
            continue
        if re.match(r"^\s*<!--.*-->\s*$", line):
            continue
        if re.match(r"^\s*<!--", line) and "-->" not in line:
            in_comment_block = True
            continue
        if in_comment_block:
            if "-->" in line:
                in_comment_block = False
            continue
        prose_lines.append(line)
    prose = "\n".join(prose_lines).strip()
    prose = re.sub(r"\n---\s*$", "", prose)
    return prose


def extract_prose_from_translation(md: str) -> str:
    """
    Translation files are markdown with:
    - title heading
    - HTML comments for meta
    - prose
    """
    lines = md.splitlines()
    out: list[str] = []
    for line in lines:
        if TITLE_RE.match(line):
            continue
        if re.match(r"^\s*<!--.*-->\s*$", line):
            continue
        out.append(line)
    prose = "\n".join(out).strip()
    prose = re.sub(r"\n---\s*$", "", prose)
    return prose


def split_paragraphs(prose: str) -> list[str]:
    paras = re.split(r"\n\s*\n", prose)
    return [p for p in (para.rstrip() for para in paras) if p.strip() != ""]


def is_scene_break(block: str) -> bool:
    s = block.strip()
    return s in {"---", "***"} or re.fullmatch(r"\*\s*\*\s*\*", s) is not None


def load_protected_tokens(cfg: dict[str, Any]) -> list[str]:
    prot = cfg.get("protected", {}) or {}
    tokens: list[str] = list(prot.get("tokens", []) or [])

    if prot.get("include_entities_registry", False) and ENTITIES_PATH.exists():
        try:
            ent = load_yaml(ENTITIES_PATH)
            tokens.extend(ent.get("do_not_translate_tokens", []) or [])
        except Exception:
            pass

    satya_terms: list[str] = list(prot.get("satya_terms", []) or [])
    for t in satya_terms:
        tokens.append(t)
        tokens.append(f"*{t}*")

    return sorted(set(tokens), key=len, reverse=True)


def is_ascii_word(tok: str) -> bool:
    # Treat only ASCII "word" tokens as needing boundary-aware checks. This works for CJK text where
    # Latin tokens may appear adjacent to CJK characters without spaces (e.g. "Kael把...").
    return re.fullmatch(r"[A-Za-z0-9_]+", tok) is not None


def qc(*, src_blocks: list[str], mt_blocks: list[str], protected_tokens: list[str]) -> QCResult:
    issues: list[str] = []

    if len(src_blocks) != len(mt_blocks):
        issues.append(f"[STRUCTURE] Paragraph count mismatch: src={len(src_blocks)} mt={len(mt_blocks)}")

    # Compare scene-break positions (best-effort).
    for i in range(min(len(src_blocks), len(mt_blocks))):
        if is_scene_break(src_blocks[i]) != is_scene_break(mt_blocks[i]):
            issues.append(f"[STRUCTURE] Scene-break mismatch at block {i+1}")

    # Token checks: only require tokens that appear in source overall.
    src_all = "\n\n".join(src_blocks)
    mt_all = "\n\n".join(mt_blocks)
    for tok in protected_tokens:
        if is_ascii_word(tok):
            # Use ASCII boundaries so `Kael` in `Kael把...` counts as present.
            in_src = re.search(rf"(?<![A-Za-z0-9_]){re.escape(tok)}(?![A-Za-z0-9_])", src_all) is not None
            in_mt = re.search(rf"(?<![A-Za-z0-9_]){re.escape(tok)}(?![A-Za-z0-9_])", mt_all) is not None
        else:
            in_src = tok in src_all
            in_mt = tok in mt_all
        if in_src and not in_mt:
            issues.append(f"[TOKENS] Missing protected token in MT: {tok!r}")

    if re.search(r"(?:_{1,3}|\[\[|\[)\s*PROT\d{3}\s*(?:_{1,3}|\]\]|\])", mt_all):
        issues.append("[TOKENS] Placeholder(s) found in MT output (PROT placeholder left behind).")

    stats = {
        "src_blocks": len(src_blocks),
        "mt_blocks": len(mt_blocks),
        "src_chars": len(src_all),
        "mt_chars": len(mt_all),
    }
    return QCResult(ok=len(issues) == 0, issues=issues, stats=stats)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="Source chapter (.draft.md)")
    ap.add_argument("--mt", required=True, help="Translated chapter (.md in translations/)")
    ap.add_argument("--cfg", default=str(PIPELINE_CFG), help="Pipeline config (for protected tokens)")
    ap.add_argument("--json", action="store_true", help="Emit JSON to stdout")
    args = ap.parse_args()

    cfg = load_yaml(Path(args.cfg))
    protected_tokens = load_protected_tokens(cfg)

    src_text = Path(args.src).read_text(encoding="utf-8")
    mt_text = Path(args.mt).read_text(encoding="utf-8")

    src_prose = extract_prose_from_draft(src_text)
    mt_prose = extract_prose_from_translation(mt_text)
    src_blocks = split_paragraphs(src_prose)
    mt_blocks = split_paragraphs(mt_prose)

    res = qc(src_blocks=src_blocks, mt_blocks=mt_blocks, protected_tokens=protected_tokens)
    if args.json:
        print(json.dumps({"ok": res.ok, "issues": res.issues, "stats": res.stats}, ensure_ascii=True, indent=2))
    else:
        if res.ok:
            print("OK")
        else:
            for issue in res.issues:
                print(issue)
    return 0 if res.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
