#!/usr/bin/env python3
"""
Apply @illust/@diagram markers to chapter drafts from a YAML plan.

This is intentionally "dumb but deterministic": the plan specifies anchors or
exact replacements so the tool can modify drafts without hidden state.

Supported marker formats (expanded by build/convert.py):
  - <!-- @illust full|thumb|link: id | text -->
  - <!-- @diagram full|thumb|link: id | text -->

Plan formats accepted:
  1) Single-chapter:
       { version, chapter, draft_path, inserts: [...] }
  2) Multi-chapter:
       { version, chapters: [{chapter, draft_path, inserts: [...]}, ...] }
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


MARKER_ID_RE = re.compile(r"<!--\s*@(illust|diagram)\s+(full|thumb|link):\s*([a-z0-9_-]+)\b", re.I)


def _split_chunks(text: str) -> list[str]:
    # Keep exact blank-line runs so we don't reformat more than necessary.
    return re.split(r"(\n\n+)", text)


def _find_para_indexes(chunks: list[str], needle: str) -> list[int]:
    idxs: list[int] = []
    for i in range(0, len(chunks), 2):  # paragraph chunks are even indexes
        if needle in chunks[i]:
            idxs.append(i)
    return idxs


def _apply_insert_after(text: str, *, anchor: str, marker: str, occurrence: int | None) -> str:
    chunks = _split_chunks(text)
    idxs = _find_para_indexes(chunks, anchor)
    if not idxs:
        raise ValueError(f'anchor not found for after_paragraph_including: {anchor!r}')
    if occurrence is None:
        if len(idxs) != 1:
            raise ValueError(f'anchor matched {len(idxs)} paragraphs; add apply.occurrence to disambiguate: {anchor!r}')
        i = idxs[0]
    else:
        if occurrence < 1 or occurrence > len(idxs):
            raise ValueError(f"occurrence out of range: {occurrence} (matches: {len(idxs)}) for {anchor!r}")
        i = idxs[occurrence - 1]

    if i + 1 < len(chunks):
        sep = chunks[i + 1]
        insert_at = i + 2  # after the separator following the paragraph
        chunks[insert_at:insert_at] = [marker, sep]
    else:
        # Paragraph is last; create a separator before the marker.
        sep = "\n\n"
        chunks.extend([sep, marker])
    return "".join(chunks)


def _apply_insert_before(text: str, *, anchor: str, marker: str, occurrence: int | None) -> str:
    chunks = _split_chunks(text)
    idxs = _find_para_indexes(chunks, anchor)
    if not idxs:
        raise ValueError(f'anchor not found for before_paragraph_including: {anchor!r}')
    if occurrence is None:
        if len(idxs) != 1:
            raise ValueError(f'anchor matched {len(idxs)} paragraphs; add apply.occurrence to disambiguate: {anchor!r}')
        i = idxs[0]
    else:
        if occurrence < 1 or occurrence > len(idxs):
            raise ValueError(f"occurrence out of range: {occurrence} (matches: {len(idxs)}) for {anchor!r}")
        i = idxs[occurrence - 1]

    sep = chunks[i - 1] if i > 0 else "\n\n"
    chunks[i:i] = [marker, sep]
    return "".join(chunks)

def _apply_inline_after(text: str, *, anchor: str, marker: str, occurrence: int | None) -> str:
    chunks = _split_chunks(text)
    idxs = _find_para_indexes(chunks, anchor)
    if not idxs:
        raise ValueError(f'anchor not found for after_paragraph_including: {anchor!r}')
    if occurrence is None:
        if len(idxs) != 1:
            raise ValueError(f'anchor matched {len(idxs)} paragraphs; add apply.occurrence to disambiguate: {anchor!r}')
        i = idxs[0]
    else:
        if occurrence < 1 or occurrence > len(idxs):
            raise ValueError(f"occurrence out of range: {occurrence} (matches: {len(idxs)}) for {anchor!r}")
        i = idxs[occurrence - 1]

    para = chunks[i]
    m = re.search(r"(\s*)\Z", para)
    tail_ws = m.group(1) if m else ""
    head = para[: m.start()] if m else para
    joiner = "" if not head or head.endswith((" ", "\t")) else " "
    chunks[i] = f"{head}{joiner}{marker}{tail_ws}"
    return "".join(chunks)


def _apply_inline_before(text: str, *, anchor: str, marker: str, occurrence: int | None) -> str:
    chunks = _split_chunks(text)
    idxs = _find_para_indexes(chunks, anchor)
    if not idxs:
        raise ValueError(f'anchor not found for before_paragraph_including: {anchor!r}')
    if occurrence is None:
        if len(idxs) != 1:
            raise ValueError(f'anchor matched {len(idxs)} paragraphs; add apply.occurrence to disambiguate: {anchor!r}')
        i = idxs[0]
    else:
        if occurrence < 1 or occurrence > len(idxs):
            raise ValueError(f"occurrence out of range: {occurrence} (matches: {len(idxs)}) for {anchor!r}")
        i = idxs[occurrence - 1]

    para = chunks[i]
    m = re.match(r"^(\s*)", para)
    lead_ws = m.group(1) if m else ""
    rest = para[len(lead_ws) :]
    joiner = "" if not rest or rest.startswith((" ", "\t")) else " "
    chunks[i] = f"{lead_ws}{marker}{joiner}{rest}"
    return "".join(chunks)


def _apply_replace_exact(text: str, *, old: str, marker: str) -> str:
    count = text.count(old)
    if count == 0:
        raise ValueError(f"replace_exact not found: {old!r}")
    if count != 1:
        raise ValueError(f"replace_exact matched {count} times (must be exactly 1): {old!r}")
    return text.replace(old, marker, 1)


def _normalize_plan(data: object) -> list[dict]:
    if not isinstance(data, dict):
        raise ValueError("plan must be a YAML mapping/object at the top level")
    if "chapters" in data:
        chapters = data.get("chapters")
        if not isinstance(chapters, list):
            raise ValueError("plan.chapters must be a list")
        return chapters
    # Single chapter plan
    return [data]


def _marker_for(insert: dict) -> str:
    kind = str(insert.get("kind") or "").strip().lower()
    typ = str(insert.get("type") or "").strip().lower()
    ins_id = str(insert.get("id") or "").strip()
    text = str(insert.get("text") or "").strip()

    if kind not in {"illust", "diagram"}:
        raise ValueError(f"insert.kind must be illust|diagram (got {kind!r})")
    if typ not in {"full", "thumb", "link"}:
        raise ValueError(f"insert.type must be full|thumb|link (got {typ!r})")
    if not re.fullmatch(r"[a-z0-9_-]+", ins_id):
        raise ValueError(f"insert.id must match [a-z0-9_-]+ (got {ins_id!r})")
    if not text:
        raise ValueError("insert.text is required (caption/alt/link text)")
    return f"<!-- @{kind} {typ}: {ins_id} | {text} -->"


def _already_present(text: str, ins_id: str) -> bool:
    for m in MARKER_ID_RE.finditer(text):
        if m.group(3).lower() == ins_id.lower():
            return True
    return False


def _apply_one_insert(text: str, insert: dict) -> tuple[str, bool]:
    ins_id = str(insert.get("id") or "").strip()
    marker = _marker_for(insert)
    typ = str(insert.get("type") or "").strip().lower()

    if _already_present(text, ins_id):
        return text, False

    apply = insert.get("apply")
    if not isinstance(apply, dict):
        raise ValueError(f"insert.apply must be a mapping for id={ins_id}")

    # Optional disambiguation for after/before anchors.
    occ = apply.get("occurrence")
    occurrence = int(occ) if occ is not None else None

    keys = [k for k, v in apply.items() if v is not None and k != "occurrence"]
    if len(keys) != 1:
        raise ValueError(f"insert.apply must contain exactly 1 mode key (got {keys}) for id={ins_id}")

    mode = keys[0]
    value = str(apply.get(mode) or "")
    if not value:
        raise ValueError(f"insert.apply.{mode} must be a non-empty string for id={ins_id}")

    # Enforce sane apply modes by marker type.
    if typ == "link" and mode != "replace_exact":
        raise ValueError(f"link inserts must use apply.replace_exact (id={ins_id})")
    if typ == "full" and mode == "replace_exact":
        raise ValueError(f"full inserts must not use apply.replace_exact (id={ins_id})")

    out = text
    if mode == "after_paragraph_including":
        if typ == "full":
            out = _apply_insert_after(out, anchor=value, marker=marker, occurrence=occurrence)
        else:
            out = _apply_inline_after(out, anchor=value, marker=marker, occurrence=occurrence)
    elif mode == "before_paragraph_including":
        if typ == "full":
            out = _apply_insert_before(out, anchor=value, marker=marker, occurrence=occurrence)
        else:
            out = _apply_inline_before(out, anchor=value, marker=marker, occurrence=occurrence)
    elif mode == "replace_exact":
        out = _apply_replace_exact(out, old=value, marker=marker)
    else:
        raise ValueError(f"unknown apply mode: {mode!r} for id={ins_id}")

    return out, (out != text)


def _load_yaml(path: Path) -> object:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--plan",
        default="agents/visual/visual-inserts.yaml",
        help="YAML plan path (relative to book root unless absolute)",
    )
    ap.add_argument("--write", action="store_true", help="Write changes in-place")
    args = ap.parse_args(argv)

    plan_path = Path(args.plan)
    if not plan_path.is_absolute():
        plan_path = ROOT / plan_path
    if not plan_path.is_file():
        print(f"error: plan not found: {plan_path}", file=sys.stderr)
        return 2

    try:
        data = _load_yaml(plan_path)
        chapters = _normalize_plan(data)
    except Exception as e:
        print(f"error: invalid plan: {e}", file=sys.stderr)
        return 2

    any_changes = False
    for ch in chapters:
        if not isinstance(ch, dict):
            print("error: chapter entry must be a mapping", file=sys.stderr)
            return 2

        draft_path = ch.get("draft_path") or ch.get("path") or ch.get("draft")
        if not draft_path:
            print("error: chapter entry missing draft_path", file=sys.stderr)
            return 2
        draft = Path(str(draft_path))
        if not draft.is_absolute():
            draft = ROOT / draft
        if not draft.is_file():
            print(f"error: draft not found: {draft}", file=sys.stderr)
            return 2

        inserts = ch.get("inserts")
        if inserts is None:
            inserts = []
        if not isinstance(inserts, list):
            print(f"error: inserts must be a list for draft {draft}", file=sys.stderr)
            return 2

        original = draft.read_text(encoding="utf-8")
        updated = original

        for ins in inserts:
            if not isinstance(ins, dict):
                print(f"error: insert must be a mapping for draft {draft}", file=sys.stderr)
                return 2
            try:
                updated, changed = _apply_one_insert(updated, ins)
            except Exception as e:
                print(f"error: {draft}: {e}", file=sys.stderr)
                return 2

            if changed:
                any_changes = True

        if args.write and updated != original:
            # Ensure the file ends with a newline (common convention).
            if not updated.endswith("\n"):
                updated += "\n"
            draft.write_text(updated, encoding="utf-8")

    if not args.write:
        # In dry-run mode, exit 1 if changes would occur (useful for CI-style checks).
        return 1 if any_changes else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
