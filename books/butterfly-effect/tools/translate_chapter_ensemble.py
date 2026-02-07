#!/usr/bin/env python3
"""
Multi-engine local translation for Sundering chapter drafts.

Goal: "1000 minds" robustness without relying on a single model.
- Generate candidates from multiple MT engines (local GPU).
- Select the best via QE/scoring (COMETKiwi when available; embedding fallback otherwise).
- Preserve formatting: scene breaks, blockquotes, and protected tokens (names, acronyms, Satya terms).

Usage:
  python3 tools/translate_chapter_ensemble.py --chapter manuscript/arc-1/chapter-01.draft.md --lang hi es

Notes:
- COMETKiwi QE models may require HuggingFace license acceptance + HF token.
- This script is intentionally conservative: default selection is one engine per chapter to avoid style drift.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import torch
import yaml
from transformers import (
    AutoModel,
    AutoModelForSeq2SeqLM,
    AutoProcessor,
    AutoTokenizer,
    SeamlessM4Tv2ForTextToText,
)


ROOT = Path(__file__).resolve().parents[1]
CFG_PATH = ROOT / "agents/translation/translation-pipeline.yaml"
ENTITIES_PATH = ROOT / "schema/entities.yaml"

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


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


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


def split_paragraphs(prose: str) -> list[str]:
    paras = re.split(r"\n\s*\n", prose)
    return [p for p in (para.rstrip() for para in paras) if p.strip() != ""]


def is_scene_break(block: str) -> bool:
    s = block.strip()
    return s in {"---", "***"} or re.fullmatch(r"\*\s*\*\s*\*", s) is not None


def is_blockquote_block(block: str) -> bool:
    lines = block.splitlines()
    # Blockquote blocks are often contiguous groups of "> " lines.
    return bool(lines) and all(l.lstrip().startswith("> ") for l in lines if l.strip())


def make_placeholders(tokens: list[str]) -> tuple[list[str], dict[str, str]]:
    sorted_tokens = sorted(set(tokens), key=len, reverse=True)
    mapping: dict[str, str] = {}
    for i, tok in enumerate(sorted_tokens):
        # Underscores tend to survive MT unchanged, unlike bracket-heavy tokens.
        mapping[f"__PROT{i:03d}__"] = tok
    return sorted_tokens, mapping


def protect_text(text: str, ph_map: dict[str, str]) -> str:
    out = text
    for ph, tok in ph_map.items():
        # Whole-token replacement for word-ish tokens prevents substring corruption
        # (e.g. Satya "mati" inside English word "formation").
        if re.fullmatch(r"[A-Za-z0-9_]+", tok):
            # ASCII boundaries so tokens can be adjacent to CJK characters without spaces.
            out = re.sub(rf"(?<![A-Za-z0-9_]){re.escape(tok)}(?![A-Za-z0-9_])", ph, out)
        else:
            out = out.replace(tok, ph)
    return out


def unprotect_text(text: str, ph_map: dict[str, str]) -> str:
    out = text
    for ph, tok in ph_map.items():
        code = ph.strip("_")  # "PROT000"

        # Exact placeholder.
        out = out.replace(ph, tok)

        # Common model "normalizations".
        out = re.sub(rf"_{1,3}\s*{re.escape(code)}\s*_{1,3}", tok, out)
        out = re.sub(rf"\[\[\s*{re.escape(code)}\s*\]\]", tok, out)
        out = re.sub(rf"\[\s*{re.escape(code)}\s*\]", tok, out)
    return out


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def pick_device(pref: str) -> str:
    if pref == "cpu":
        return "cpu"
    if pref == "cuda":
        return "cuda" if torch.cuda.is_available() else "cpu"
    # auto
    return "cuda" if torch.cuda.is_available() else "cpu"


class Engine:
    id: str

    def supports(self, lang: str) -> bool:
        raise NotImplementedError

    def translate(self, blocks: list[str], *, lang: str, ph_map: dict[str, str]) -> list[str]:
        raise NotImplementedError

    def close(self) -> None:
        pass


class NLLBEngine(Engine):
    def __init__(self, *, engine_id: str, model_name: str, source_lang: str, targets: dict[str, str], generate: dict[str, Any], device: str) -> None:
        self.id = engine_id
        self.model_name = model_name
        self.source_lang = source_lang
        self.targets = targets
        self.num_beams = int(generate.get("num_beams", 5))
        self.max_new_tokens = int(generate.get("max_new_tokens", 512))
        self.device = device

        dtype = torch.float32 if device == "cpu" else torch.float16
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            model_name,
            torch_dtype=dtype,
            device_map="auto" if device == "cuda" else None,
        )
        if device == "cpu":
            self.model = self.model.to(device)
        self.model.eval()

    def supports(self, lang: str) -> bool:
        return lang in self.targets

    def translate(self, blocks: list[str], *, lang: str, ph_map: dict[str, str]) -> list[str]:
        tgt_lang = self.targets[lang]
        self.tokenizer.src_lang = self.source_lang
        forced_bos_token_id = self.tokenizer.convert_tokens_to_ids(tgt_lang)

        out_blocks: list[str] = []
        for b in blocks:
            if is_scene_break(b):
                out_blocks.append(b.strip())
                continue

            if is_blockquote_block(b):
                translated_lines: list[str] = []
                for line in b.splitlines():
                    if not line.strip():
                        translated_lines.append(line)
                        continue
                    prefix = line.split("> ", 1)[0] + "> "
                    content = line.split("> ", 1)[1]
                    protected = protect_text(content, ph_map)
                    inp = self.tokenizer(protected, return_tensors="pt", truncation=True).to(self.device)
                    gen = self.model.generate(
                        **inp,
                        forced_bos_token_id=forced_bos_token_id,
                        num_beams=self.num_beams,
                        max_new_tokens=self.max_new_tokens,
                    )
                    out = self.tokenizer.batch_decode(gen, skip_special_tokens=True)[0]
                    out = unprotect_text(out, ph_map).strip()
                    translated_lines.append(prefix + out)
                out_blocks.append("\n".join(translated_lines).rstrip())
                continue

            protected = protect_text(b, ph_map)
            inp = self.tokenizer(protected, return_tensors="pt", truncation=True).to(self.device)
            gen = self.model.generate(
                **inp,
                forced_bos_token_id=forced_bos_token_id,
                num_beams=self.num_beams,
                max_new_tokens=self.max_new_tokens,
            )
            out = self.tokenizer.batch_decode(gen, skip_special_tokens=True)[0]
            out = unprotect_text(out, ph_map).strip()
            out_blocks.append(out)

        return out_blocks

    def close(self) -> None:
        del self.model
        del self.tokenizer
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


class SeamlessV2Engine(Engine):
    def __init__(self, *, engine_id: str, model_name: str, targets: dict[str, str], generate: dict[str, Any], device: str) -> None:
        self.id = engine_id
        self.model_name = model_name
        self.targets = targets
        self.num_beams = int(generate.get("num_beams", 5))
        self.max_new_tokens = int(generate.get("max_new_tokens", 512))
        self.device = device

        dtype = torch.float32 if device == "cpu" else torch.float16
        self.processor = AutoProcessor.from_pretrained(model_name)
        self.model = SeamlessM4Tv2ForTextToText.from_pretrained(
            model_name,
            torch_dtype=dtype,
            device_map="auto" if device == "cuda" else None,
        )
        if device == "cpu":
            self.model = self.model.to(device)
        self.model.eval()

    def supports(self, lang: str) -> bool:
        return lang in self.targets

    def translate(self, blocks: list[str], *, lang: str, ph_map: dict[str, str]) -> list[str]:
        tgt_lang = self.targets[lang]
        out_blocks: list[str] = []

        for b in blocks:
            if is_scene_break(b):
                out_blocks.append(b.strip())
                continue

            if is_blockquote_block(b):
                translated_lines: list[str] = []
                for line in b.splitlines():
                    if not line.strip():
                        translated_lines.append(line)
                        continue
                    prefix = line.split("> ", 1)[0] + "> "
                    content = line.split("> ", 1)[1]
                    protected = protect_text(content, ph_map)
                    inp = self.processor(text=protected, return_tensors="pt").to(self.device)
                    gen = self.model.generate(
                        **inp,
                        tgt_lang=tgt_lang,
                        num_beams=self.num_beams,
                        max_new_tokens=self.max_new_tokens,
                    )
                    out = self.processor.batch_decode(gen, skip_special_tokens=True)[0]
                    out = unprotect_text(out, ph_map).strip()
                    translated_lines.append(prefix + out)
                out_blocks.append("\n".join(translated_lines).rstrip())
                continue

            protected = protect_text(b, ph_map)
            inp = self.processor(text=protected, return_tensors="pt").to(self.device)
            gen = self.model.generate(
                **inp,
                tgt_lang=tgt_lang,
                num_beams=self.num_beams,
                max_new_tokens=self.max_new_tokens,
            )
            out = self.processor.batch_decode(gen, skip_special_tokens=True)[0]
            out = unprotect_text(out, ph_map).strip()
            out_blocks.append(out)

        return out_blocks

    def close(self) -> None:
        del self.model
        del self.processor
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


class MadladEngine(Engine):
    def __init__(self, *, engine_id: str, model_name: str, targets: dict[str, str], generate: dict[str, Any], device: str, load_in_4bit: bool) -> None:
        self.id = engine_id
        self.model_name = model_name
        self.targets = targets
        self.num_beams = int(generate.get("num_beams", 5))
        self.max_new_tokens = int(generate.get("max_new_tokens", 512))
        self.device = device

        self.tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)
        dtype = torch.float32 if device == "cpu" else torch.float16

        if load_in_4bit and device == "cuda":
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                model_name,
                torch_dtype=dtype,
                device_map="auto",
                load_in_4bit=True,
            )
        else:
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                model_name,
                torch_dtype=dtype,
                device_map="auto" if device == "cuda" else None,
            )
            if device == "cpu":
                self.model = self.model.to(device)

        self.model.eval()

    def supports(self, lang: str) -> bool:
        return lang in self.targets

    def translate(self, blocks: list[str], *, lang: str, ph_map: dict[str, str]) -> list[str]:
        prefix = self.targets[lang].strip()
        out_blocks: list[str] = []

        for b in blocks:
            if is_scene_break(b):
                out_blocks.append(b.strip())
                continue

            if is_blockquote_block(b):
                translated_lines: list[str] = []
                for line in b.splitlines():
                    if not line.strip():
                        translated_lines.append(line)
                        continue
                    bq_prefix = line.split("> ", 1)[0] + "> "
                    content = line.split("> ", 1)[1]
                    protected = protect_text(content, ph_map)
                    inp = self.tokenizer(f"{prefix} {protected}", return_tensors="pt", truncation=True).to(self.device)
                    gen = self.model.generate(
                        **inp,
                        num_beams=self.num_beams,
                        max_new_tokens=self.max_new_tokens,
                    )
                    out = self.tokenizer.batch_decode(gen, skip_special_tokens=True)[0]
                    out = unprotect_text(out, ph_map).strip()
                    translated_lines.append(bq_prefix + out)
                out_blocks.append("\n".join(translated_lines).rstrip())
                continue

            protected = protect_text(b, ph_map)
            inp = self.tokenizer(f"{prefix} {protected}", return_tensors="pt", truncation=True).to(self.device)
            gen = self.model.generate(
                **inp,
                num_beams=self.num_beams,
                max_new_tokens=self.max_new_tokens,
            )
            out = self.tokenizer.batch_decode(gen, skip_special_tokens=True)[0]
            out = unprotect_text(out, ph_map).strip()
            out_blocks.append(out)

        return out_blocks

    def close(self) -> None:
        del self.model
        del self.tokenizer
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


class EmbedFallbackScorer:
    def __init__(self, *, model_name: str, device: str, batch_size: int) -> None:
        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size

        dtype = torch.float32 if device == "cpu" else torch.float16
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name, torch_dtype=dtype)
        self.model = self.model.to(device)
        self.model.eval()

    @staticmethod
    def _mean_pool(last_hidden: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        mask = mask.unsqueeze(-1).type_as(last_hidden)
        summed = (last_hidden * mask).sum(dim=1)
        denom = mask.sum(dim=1).clamp(min=1e-6)
        return summed / denom

    def embed(self, texts: list[str]) -> torch.Tensor:
        embs: list[torch.Tensor] = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            tok = self.tokenizer(batch, return_tensors="pt", padding=True, truncation=True, max_length=512).to(self.device)
            with torch.no_grad():
                out = self.model(**tok)
            pooled = self._mean_pool(out.last_hidden_state, tok["attention_mask"])
            pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)
            embs.append(pooled.detach().cpu())
        return torch.cat(embs, dim=0)

    def score_pairs(self, *, src: list[str], mt: list[str]) -> list[float]:
        # E5-style prefixes (helps some checkpoints behave better).
        src_in = [f"query: {t}" for t in src]
        mt_in = [f"passage: {t}" for t in mt]
        src_emb = self.embed(src_in)
        mt_emb = self.embed(mt_in)
        sims = (src_emb * mt_emb).sum(dim=1)
        return [float(x) for x in sims.tolist()]

    def close(self) -> None:
        del self.model
        del self.tokenizer
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


def try_load_cometkiwi(model_name: str) -> Any | None:
    """
    Optional research-grade QE scorer.
    Requires `unbabel-comet` / `comet` and typically HF license acceptance.
    """
    try:
        from comet import download_model, load_from_checkpoint  # type: ignore
    except Exception:
        return None

    try:
        ckpt = download_model(model_name)
        return load_from_checkpoint(ckpt)
    except Exception:
        return None


def cometkiwi_scores(model: Any, *, src: list[str], mt: list[str], batch_size: int, device: str) -> list[float]:
    data = [{"src": s, "mt": m} for s, m in zip(src, mt)]
    # COMET uses Lightning internally. Keep it simple: request 1 GPU if available.
    if device == "cuda" and torch.cuda.is_available():
        pred = model.predict(data, batch_size=batch_size, gpus=1)
    else:
        pred = model.predict(data, batch_size=batch_size, gpus=0)
    # `pred` is a dict-like with "scores"
    scores = pred.get("scores", pred)
    return [float(x) for x in scores]


def compute_penalties(*, src_block: str, mt_block: str, protected_tokens: Iterable[str]) -> float:
    penalty = 0.0
    if re.search(r"(?:_{1,3}|\[\[|\[)\s*PROT\d{3}\s*(?:_{1,3}|\]\]|\])", mt_block):
        penalty -= 0.6

    # If a protected token appears in the source block but not in the MT block, penalize hard.
    for tok in protected_tokens:
        if re.fullmatch(r"[A-Za-z0-9_]+", tok):
            in_src = re.search(rf"(?<![A-Za-z0-9_]){re.escape(tok)}(?![A-Za-z0-9_])", src_block) is not None
            in_mt = re.search(rf"(?<![A-Za-z0-9_]){re.escape(tok)}(?![A-Za-z0-9_])", mt_block) is not None
        else:
            in_src = tok in src_block
            in_mt = tok in mt_block
        if in_src and not in_mt:
            penalty -= 0.4
    return penalty


def flatten_for_scoring(blocks: list[str]) -> list[str]:
    """
    For scoring, strip blockquote prefixes so the scorer focuses on content.
    """
    out: list[str] = []
    for b in blocks:
        if is_scene_break(b):
            out.append("")
            continue
        if is_blockquote_block(b):
            lines = []
            for line in b.splitlines():
                if line.lstrip().startswith("> "):
                    lines.append(line.split("> ", 1)[1])
                else:
                    lines.append(line)
            out.append("\n".join(lines).strip())
            continue
        out.append(b.strip())
    return out


def load_protected_tokens(cfg: dict[str, Any]) -> list[str]:
    prot = cfg.get("protected", {})
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

    # De-dupe while preserving a stable order-ish (roughly: longer first later).
    return sorted(set(tokens), key=len, reverse=True)


def build_engines(cfg: dict[str, Any], *, device: str) -> dict[str, dict[str, Any]]:
    engines: dict[str, dict[str, Any]] = cfg.get("engines", {}) or {}
    enabled = {k: v for k, v in engines.items() if v and v.get("enabled", True)}
    # Inject id
    for k, v in enabled.items():
        v["id"] = k
    return enabled


def instantiate_engine(engine_cfg: dict[str, Any], *, device: str) -> Engine:
    etype = engine_cfg["type"]
    engine_id = engine_cfg["id"]
    model = engine_cfg["model"]
    targets = engine_cfg.get("targets", {}) or {}
    generate = engine_cfg.get("generate", {}) or {}

    if etype == "nllb-200":
        return NLLBEngine(
            engine_id=engine_id,
            model_name=model,
            source_lang=engine_cfg["source_lang"],
            targets=targets,
            generate=generate,
            device=device,
        )
    if etype == "seamless-m4t-v2-text":
        return SeamlessV2Engine(
            engine_id=engine_id,
            model_name=model,
            targets=targets,
            generate=generate,
            device=device,
        )
    if etype == "madlad400":
        return MadladEngine(
            engine_id=engine_id,
            model_name=model,
            targets=targets,
            generate=generate,
            device=device,
            load_in_4bit=bool(engine_cfg.get("load_in_4bit", False)),
        )
    raise ValueError(f"Unknown engine type: {etype}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", required=True, help="Path to .draft.md")
    ap.add_argument("--lang", nargs="+", default=None, help="Target languages (default: all in config)")
    ap.add_argument("--device", default="auto", choices=["auto", "cuda", "cpu"])
    ap.add_argument("--cfg", default=str(CFG_PATH), help="Path to translation pipeline YAML")
    ap.add_argument("--engines", nargs="+", default=None, help="Engine ids to use (default: enabled engines)")
    args = ap.parse_args()

    cfg = load_yaml(Path(args.cfg))

    # HuggingFace cache (avoid re-downloading).
    os.environ.setdefault("HF_HOME", str(ROOT / ".hf-cache"))

    device = pick_device(args.device)
    selection_mode = (cfg.get("selection", {}) or {}).get("mode", "chapter")
    if selection_mode not in {"chapter", "paragraph"}:
        raise SystemExit(f"Unsupported selection.mode={selection_mode!r} (expected 'chapter' or 'paragraph')")

    # Determine languages
    targets_cfg = cfg.get("targets", []) or []
    supported_langs = [t["id"] for t in targets_cfg if isinstance(t, dict) and "id" in t]
    langs = args.lang or supported_langs
    unknown = [l for l in langs if l not in supported_langs]
    if unknown:
        raise SystemExit(f"Unknown language(s): {', '.join(unknown)} (add to {Path(args.cfg).relative_to(ROOT)})")

    # Prepare chapter inputs
    chapter_path = Path(args.chapter)
    draft_text = chapter_path.read_text(encoding="utf-8")
    meta = parse_chapter_meta(draft_text)
    prose = extract_prose(draft_text)
    blocks = split_paragraphs(prose)
    score_src_blocks = flatten_for_scoring(blocks)

    protected_tokens = load_protected_tokens(cfg)
    _, ph_map = make_placeholders(protected_tokens)

    engines_cfg_all = build_engines(cfg, device=device)
    if args.engines:
        engines_cfg = {k: v for k, v in engines_cfg_all.items() if k in set(args.engines)}
        missing = [k for k in args.engines if k not in engines_cfg_all]
        if missing:
            raise SystemExit(f"Unknown engine id(s): {', '.join(missing)}")
    else:
        engines_cfg = engines_cfg_all

    if not engines_cfg:
        raise SystemExit("No enabled engines found in config.")

    # Generate candidates: candidates[lang][engine_id] = list[str]
    candidates: dict[str, dict[str, list[str]]] = {l: {} for l in langs}
    title_candidates: dict[str, dict[str, str]] = {l: {} for l in langs}

    for engine_id, engine_cfg in engines_cfg.items():
        try:
            eng = instantiate_engine(engine_cfg, device=device)
        except Exception as e:
            sys.stderr.write(f"[engine] skip engine={engine_id} (load failed): {type(e).__name__}: {e}\n")
            continue
        try:
            for lang in langs:
                if not eng.supports(lang):
                    continue
                sys.stderr.write(f"[translate] engine={engine_id} lang={lang}\n")
                try:
                    title_candidates[lang][engine_id] = eng.translate([meta.title], lang=lang, ph_map=ph_map)[0].strip()
                except Exception:
                    title_candidates[lang][engine_id] = meta.title
                out = eng.translate(blocks, lang=lang, ph_map=ph_map)
                candidates[lang][engine_id] = out
        finally:
            eng.close()

    # Scoring: prefer COMETKiwi if enabled and available, else embedding similarity
    qe_cfg = cfg.get("qe", {}) or {}
    comet_cfg = qe_cfg.get("cometkiwi", {}) or {}
    embed_cfg = qe_cfg.get("embed_fallback", {}) or {}

    comet_model = None
    comet_enabled = bool(comet_cfg.get("enabled", False))
    if comet_enabled:
        comet_model = try_load_cometkiwi(str(comet_cfg.get("model", "")))
        if comet_model is None:
            sys.stderr.write("[qe] COMETKiwi unavailable (missing deps, HF access, or license acceptance). Falling back.\n")
            comet_enabled = False

    embed_enabled = bool(embed_cfg.get("enabled", True))
    embed_scorer = None
    if not comet_enabled and embed_enabled:
        embed_device = pick_device(str(embed_cfg.get("device", "auto")))
        # Keep GPU memory available for MT by running fallback scoring after MT models are closed.
        embed_scorer = EmbedFallbackScorer(
            model_name=str(embed_cfg.get("model", "intfloat/multilingual-e5-small")),
            device=embed_device,
            batch_size=int(embed_cfg.get("batch_size", 16)),
        )

    # For each language: compute per-engine scores, select, write output + report
    out_root = ROOT / str((cfg.get("io", {}) or {}).get("output_root", "translations"))
    ensure_dir(out_root)

    for lang in langs:
        eng_map = candidates.get(lang, {})
        if not eng_map:
            sys.stderr.write(f"[warn] No candidates produced for lang={lang}\n")
            continue

        engine_ids = sorted(eng_map.keys())
        scores_by_engine: dict[str, list[float]] = {}
        avg_by_engine: dict[str, float] = {}

        for engine_id in engine_ids:
            mt_blocks = flatten_for_scoring(eng_map[engine_id])
            if comet_enabled and comet_model is not None:
                qe_device = pick_device(str(comet_cfg.get("device", "auto")))
                base_scores = cometkiwi_scores(
                    comet_model,
                    src=score_src_blocks,
                    mt=mt_blocks,
                    batch_size=int(comet_cfg.get("batch_size", 8)),
                    device=qe_device,
                )
            elif embed_scorer is not None:
                base_scores = embed_scorer.score_pairs(src=score_src_blocks, mt=mt_blocks)
            else:
                # Last resort: no scorer available. Prefer Seamless then NLLB then others by name.
                base_scores = [0.0 for _ in mt_blocks]

            penalties = [
                compute_penalties(src_block=s, mt_block=m, protected_tokens=protected_tokens)
                for s, m in zip(score_src_blocks, mt_blocks)
            ]
            final_scores = [float(b + p) for b, p in zip(base_scores, penalties)]
            scores_by_engine[engine_id] = final_scores
            avg_by_engine[engine_id] = float(sum(final_scores) / max(1, len(final_scores)))

        # Selection
        selected_engine: str
        selected_blocks: list[str]
        selection_detail: Any

        if selection_mode == "chapter":
            selected_engine = max(avg_by_engine.keys(), key=lambda k: avg_by_engine[k])
            selected_blocks = eng_map[selected_engine]
            selection_detail = {"selected_engine": selected_engine, "avg_scores": avg_by_engine}
        else:
            selected_blocks = []
            selected_engine = "mixed"
            chosen: list[str] = []
            for i in range(len(blocks)):
                best = max(engine_ids, key=lambda e: scores_by_engine[e][i])
                chosen.append(best)
                selected_blocks.append(eng_map[best][i])
            selection_detail = {"selected_engines_per_block": chosen, "avg_scores": avg_by_engine}

        # Title translation: prefer the selected engine (or Seamless if mixed).
        title_engine_id = selected_engine if selected_engine != "mixed" else ("seamless_v2" if "seamless_v2" in engines_cfg else engine_ids[0])
        translated_title = title_candidates.get(lang, {}).get(title_engine_id, meta.title)

        arc_dir = f"arc-{meta.arc}"
        ch_file = f"chapter-{meta.num:02d}.md"
        out_dir = out_root / lang / arc_dir
        ensure_dir(out_dir)
        out_path = out_dir / ch_file

        header = [
            f"# Chapter {meta.num}: {translated_title}",
            f"<!-- Arc: {meta.arc} | POV: {meta.pov} | Location: {meta.location} | Timeline: {meta.timeline} -->",
            f"<!-- Translation: {lang} | Pipeline: ensemble | Selection: {selection_mode} | Selected: {selection_detail.get('selected_engine', 'mixed')} | Device: {device} -->",
            "",
        ]
        body = "\n\n".join(selected_blocks).rstrip() + "\n"
        out_path.write_text("\n".join(header) + body, encoding="utf-8")

        report = {
            "chapter": {"arc": meta.arc, "num": meta.num, "title": meta.title, "pov": meta.pov, "location": meta.location, "timeline": meta.timeline},
            "lang": lang,
            "selection_mode": selection_mode,
            "selection": selection_detail,
            "scores": {
                "avg_by_engine": avg_by_engine,
            },
            "qe": {
                "cometkiwi_enabled": comet_enabled,
                "embed_fallback_enabled": embed_scorer is not None,
                "embed_model": getattr(embed_scorer, "model_name", None),
                "comet_model": str(comet_cfg.get("model")) if comet_enabled else None,
            },
        }
        report_path = out_path.with_suffix(".report.json")
        report_path.write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

        print(f"Wrote {out_path.relative_to(ROOT)}")
        print(f"Wrote {report_path.relative_to(ROOT)}")

    if embed_scorer is not None:
        embed_scorer.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
