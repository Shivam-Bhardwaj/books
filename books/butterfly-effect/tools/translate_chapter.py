#!/usr/bin/env python3
"""
Local GPU machine translation for Sundering chapter drafts.

Default engine: NLLB-200 (transformers).

This produces a baseline translation, then you can run a human/LLM post-edit pass
for voice and pidgin handling.
"""

from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path

import torch
import yaml
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer


ROOT = Path(__file__).resolve().parents[1]
CFG_PATH = ROOT / "agents/translation/translation-config.yaml"


TITLE_RE = re.compile(r"^# Chapter\s+(\d+):\s*(.+)$", re.MULTILINE)
META_RE = re.compile(
    r"<!--\s*Arc:\s*(\d+)\s*\|\s*POV:\s*(.+?)\s*\|\s*Location:\s*(.+?)\s*\|\s*Timeline:\s*(.+?)\s*-->",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ChapterMeta:
    arc: int
    num: int
    title: str
    pov: str
    location: str
    timeline: str


def load_cfg() -> dict:
    return yaml.safe_load(CFG_PATH.read_text(encoding="utf-8"))


def parse_chapter_meta(draft_text: str) -> ChapterMeta:
    title_m = TITLE_RE.search(draft_text)
    if not title_m:
        raise ValueError("Missing chapter title line: '# Chapter NN: Title'")
    num = int(title_m.group(1))
    title = title_m.group(2).strip()

    meta_m = META_RE.search(draft_text)
    if meta_m:
        arc = int(meta_m.group(1))
        pov = meta_m.group(2).strip()
        location = meta_m.group(3).strip()
        timeline = meta_m.group(4).strip()
    else:
        arc, pov, location, timeline = 1, "Unknown", "Unknown", "Unknown"

    return ChapterMeta(arc=arc, num=num, title=title, pov=pov, location=location, timeline=timeline)


def extract_prose(draft_text: str) -> str:
    """
    Strip draft-only scaffolding (title + HTML comments) and return prose markdown.
    Mirrors build/convert.py behavior to avoid translating beat-sheet comments.
    """
    lines = draft_text.splitlines()
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


def make_placeholders(tokens: list[str]) -> tuple[list[str], dict[str, str]]:
    """
    Returns (sorted_tokens, mapping placeholder->token).
    We do not return token->placeholder because multiple tokens can collide after normalization.
    """
    # Sort by length to avoid partial replacements (e.g., "Satya" inside "Satya-speaker")
    sorted_tokens = sorted(set(tokens), key=len, reverse=True)
    mapping: dict[str, str] = {}
    for i, tok in enumerate(sorted_tokens):
        # Use a placeholder that's unlikely to be "normalized" by MT models.
        # Underscores tend to survive MT unchanged, unlike bracket-heavy tokens.
        mapping[f"__PROT{i:03d}__"] = tok
    return sorted_tokens, mapping


def protect(text: str, tokens: list[str], ph_map: dict[str, str]) -> str:
    out = text
    # Replace tokens with placeholders deterministically.
    for ph, tok in ph_map.items():
        # Prefer whole-token replacement for word-ish tokens to avoid corrupting substrings
        # (e.g. Satya term "mati" inside English word "formation").
        if re.fullmatch(r"[A-Za-z0-9_]+", tok):
            # ASCII boundaries so tokens can be adjacent to CJK characters without spaces.
            out = re.sub(rf"(?<![A-Za-z0-9_]){re.escape(tok)}(?![A-Za-z0-9_])", ph, out)
        else:
            out = out.replace(tok, ph)
    return out


def unprotect(text: str, ph_map: dict[str, str]) -> str:
    out = text
    for ph, tok in ph_map.items():
        code = ph.strip("_")  # "PROT000"

        # Exact placeholder.
        out = out.replace(ph, tok)

        # Common model "normalizations" we observed in practice.
        out = re.sub(rf"_{1,3}\s*{re.escape(code)}\s*_{1,3}", tok, out)
        out = re.sub(rf"\[\[\s*{re.escape(code)}\s*\]\]", tok, out)
        out = re.sub(rf"\[\s*{re.escape(code)}\s*\]", tok, out)

    return out


def split_paragraphs(prose: str) -> list[str]:
    # Preserve scene breaks as standalone paragraphs.
    paras = re.split(r"\n\s*\n", prose)
    return [p for p in (para.rstrip() for para in paras) if p.strip() != ""]


def translate_blocks(
    blocks: list[str],
    *,
    tokenizer: AutoTokenizer,
    model: AutoModelForSeq2SeqLM,
    src_lang: str,
    tgt_lang: str,
    num_beams: int,
    max_new_tokens: int,
    device: str,
    protected_tokens: list[str],
    satya_terms: list[str],
) -> list[str]:
    # Protect key tokens and Satya terms (including italic form).
    tokens = list(protected_tokens)
    for t in satya_terms:
        tokens.append(t)
        tokens.append(f"*{t}*")

    sorted_tokens, ph_map = make_placeholders(tokens)

    tokenizer.src_lang = src_lang
    forced_bos_token_id = tokenizer.convert_tokens_to_ids(tgt_lang)

    out_blocks: list[str] = []
    for b in blocks:
        s = b.strip()
        if s in {"---", "***"}:
            out_blocks.append(s)
            continue

        # Blockquotes: preserve leading "> " markers line-by-line.
        lines = b.splitlines()
        if lines and all(l.lstrip().startswith("> ") for l in lines if l.strip()):
            translated_lines: list[str] = []
            for line in lines:
                if not line.strip():
                    translated_lines.append(line)
                    continue
                prefix = line.split("> ", 1)[0] + "> "
                content = line.split("> ", 1)[1]
                protected = protect(content, sorted_tokens, ph_map)
                inp = tokenizer(protected, return_tensors="pt", truncation=True).to(device)
                gen = model.generate(
                    **inp,
                    forced_bos_token_id=forced_bos_token_id,
                    num_beams=num_beams,
                    max_new_tokens=max_new_tokens,
                )
                out = tokenizer.batch_decode(gen, skip_special_tokens=True)[0]
                out = unprotect(out, ph_map).strip()
                translated_lines.append(prefix + out)
            out_blocks.append("\n".join(translated_lines).rstrip())
            continue

        protected = protect(b, sorted_tokens, ph_map)
        inp = tokenizer(protected, return_tensors="pt", truncation=True).to(device)
        gen = model.generate(
            **inp,
            forced_bos_token_id=forced_bos_token_id,
            num_beams=num_beams,
            max_new_tokens=max_new_tokens,
        )
        out = tokenizer.batch_decode(gen, skip_special_tokens=True)[0]
        out = unprotect(out, ph_map).strip()
        out_blocks.append(out)

    return out_blocks


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", required=True, help="Path to .draft.md")
    ap.add_argument("--lang", nargs="+", required=True, help="Target languages: hi es ru ar zh-hans zh-hant ko")
    ap.add_argument("--model", default=None, help="Override model name (default from config)")
    ap.add_argument("--cpu", action="store_true", help="Force CPU")
    ap.add_argument("--num-beams", type=int, default=None)
    ap.add_argument("--max-new-tokens", type=int, default=None)
    args = ap.parse_args()

    cfg = load_cfg()
    model_name = args.model or cfg["model"]["name"]
    src_lang = cfg["model"]["source_lang"]

    gen_cfg = cfg["model"].get("generate", {})
    num_beams = args.num_beams or int(gen_cfg.get("num_beams", 5))
    max_new_tokens = args.max_new_tokens or int(gen_cfg.get("max_new_tokens", 512))

    device = "cpu" if args.cpu or not torch.cuda.is_available() else "cuda"
    dtype = torch.float32 if device == "cpu" else torch.float16

    # HuggingFace cache (avoid re-downloading).
    os.environ.setdefault("HF_HOME", str(ROOT / ".hf-cache"))

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name, torch_dtype=dtype, device_map="auto" if device == "cuda" else None)
    if device == "cpu":
        model = model.to(device)
    model.eval()

    chapter_path = Path(args.chapter)
    draft_text = chapter_path.read_text(encoding="utf-8")
    meta = parse_chapter_meta(draft_text)
    prose = extract_prose(draft_text)
    blocks = split_paragraphs(prose)

    protected_tokens = cfg.get("protected", {}).get("tokens", [])
    satya_terms = cfg.get("protected", {}).get("satya_terms", [])

    # Translate title separately (keeps header readable in the target language).
    title_blocks = translate_blocks(
        [meta.title],
        tokenizer=tokenizer,
        model=model,
        src_lang=src_lang,
        tgt_lang=cfg["targets"].get("hi", "hin_Deva"),  # placeholder; overwritten per lang below
        num_beams=num_beams,
        max_new_tokens=64,
        device=device,
        protected_tokens=protected_tokens,
        satya_terms=satya_terms,
    )
    _ = title_blocks  # computed once to validate the pipeline; per-language title below.

    for lang in args.lang:
        tgt_code = cfg["targets"].get(lang)
        if not tgt_code:
            raise SystemExit(f"Unsupported lang '{lang}'. Add it to {CFG_PATH}.")

        translated_title = translate_blocks(
            [meta.title],
            tokenizer=tokenizer,
            model=model,
            src_lang=src_lang,
            tgt_lang=tgt_code,
            num_beams=num_beams,
            max_new_tokens=64,
            device=device,
            protected_tokens=protected_tokens,
            satya_terms=satya_terms,
        )[0]

        out_blocks = translate_blocks(
            blocks,
            tokenizer=tokenizer,
            model=model,
            src_lang=src_lang,
            tgt_lang=tgt_code,
            num_beams=num_beams,
            max_new_tokens=max_new_tokens,
            device=device,
            protected_tokens=protected_tokens,
            satya_terms=satya_terms,
        )

        arc_dir = f"arc-{meta.arc}"
        ch_file = f"chapter-{meta.num:02d}.md"
        out_dir = ROOT / "translations" / lang / arc_dir
        ensure_dir(out_dir)
        out_path = out_dir / ch_file

        header = [
            f"# Chapter {meta.num}: {translated_title}",
            f"<!-- Arc: {meta.arc} | POV: {meta.pov} | Location: {meta.location} | Timeline: {meta.timeline} -->",
            f"<!-- Translation: {lang} | Engine: {model_name} | Device: {device} -->",
            "",
        ]

        body = "\n\n".join(out_blocks).rstrip() + "\n"
        out_path.write_text("\n".join(header) + body, encoding="utf-8")
        print(f"Wrote {out_path.relative_to(ROOT)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
