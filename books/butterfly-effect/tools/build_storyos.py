#!/usr/bin/env python3
"""
Generate meta/storyos.json and meta/storyos.md from project sources.

Inputs:
  - schema/storyos.yaml        (hand-edited control plane)
  - schema/entities.yaml        (character/place/concept registry)
  - schema/chapter-cards.yaml   (40-chapter table)
  - book.yaml                   (title, subtitle)
  - outline/ARCS.md             (arc table cross-check)
  - outline/BUTTERFLY_GRAPH.md  (causal chains + dependency matrix)
  - review/continuity-log.md    (chapter coverage + promises)
  - review/revision-queue.md    (open/closed item counts)
  - manuscript/**/*.html        (drafted chapter count)
  - **/*.md                     (docs index)

Outputs:
  - meta/storyos.json
  - meta/storyos.md
"""
from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

# ── YAML loaders ──────────────────────────────────────────────────

def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_storyos() -> dict:
    return load_yaml(ROOT / "schema/storyos.yaml")


def load_entities() -> dict:
    return load_yaml(ROOT / "schema/entities.yaml")


def load_chapters() -> list[dict]:
    data = load_yaml(ROOT / "schema/chapter-cards.yaml")
    return data.get("chapters", [])


def load_book_meta() -> dict:
    return load_yaml(ROOT / "book.yaml")

# ── Markdown parsers ──────────────────────────────────────────────

def parse_arcs_md() -> list[dict]:
    """Parse the arc overview table from ARCS.md."""
    path = ROOT / "outline/ARCS.md"
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    arcs = []
    for m in re.finditer(
        r"\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*(\d+)\s*[–-]\s*(\d+)\s*\|",
        text,
    ):
        arcs.append({
            "id": int(m.group(1)),
            "title": m.group(2).strip(),
            "chapter_range": [int(m.group(3)), int(m.group(4))],
        })
    return arcs


def parse_butterfly_graph() -> dict:
    """Parse causal chains and dependency matrix from BUTTERFLY_GRAPH.md."""
    path = ROOT / "outline/BUTTERFLY_GRAPH.md"
    if not path.exists():
        return {"chains": {}, "dependency_matrix": []}
    text = path.read_text(encoding="utf-8")

    # Parse chains
    chains: dict[str, dict] = {}
    chain_re = re.compile(r"^## Chain ([A-F]):\s*(.+)$", re.M)
    node_re = re.compile(r"\[(\d+\.\d+|\w+.*?)\]\s*(.+?)(?:\s*$)")
    arrow_re = re.compile(r"→")

    chain_starts = list(chain_re.finditer(text))
    for idx, cm in enumerate(chain_starts):
        chain_id = cm.group(1)
        chain_title = cm.group(2).strip()
        start = cm.end()
        end = chain_starts[idx + 1].start() if idx + 1 < len(chain_starts) else text.find("## Cross-Chapter")
        if end == -1:
            end = len(text)
        block = text[start:end]

        # Find code blocks within chain
        code_blocks = re.findall(r"```\n(.*?)```", block, re.S)
        nodes = []
        edges = []
        for cb in code_blocks:
            lines = cb.strip().split("\n")
            prev_node = None
            for line in lines:
                nm = re.search(r"\[(\d+\.\d+|BACKSTORY[^]]*)\]\s*(.+?)(?:\s*$)", line)
                if nm:
                    node_id = nm.group(1).strip()
                    node_label = nm.group(2).strip()
                    nodes.append({"id": node_id, "label": node_label})
                    if "→" in line and prev_node:
                        edges.append({"from": prev_node, "to": node_id})
                    elif prev_node and line.strip().startswith("→"):
                        edges.append({"from": prev_node, "to": node_id})
                    prev_node = node_id
                elif line.strip().startswith("→") and prev_node:
                    nm2 = re.search(r"\[(\d+\.\d+|BACKSTORY[^]]*)\]\s*(.+?)(?:\s*$)", line)
                    if nm2:
                        node_id = nm2.group(1).strip()
                        node_label = nm2.group(2).strip()
                        nodes.append({"id": node_id, "label": node_label})
                        edges.append({"from": prev_node, "to": node_id})
                        prev_node = node_id

        chains[chain_id] = {
            "title": chain_title,
            "nodes": nodes,
            "edges": edges,
        }

    # Parse dependency matrix
    matrix = []
    matrix_section = text[text.find("## Cross-Chapter"):] if "## Cross-Chapter" in text else ""
    for m in re.finditer(
        r"\|\s*(\d+\.\d+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|",
        matrix_section,
    ):
        chapter_id = m.group(1).strip()
        depends = m.group(2).strip()
        feeds = m.group(3).strip()
        if depends.startswith("Depends") or depends.startswith("---"):
            continue
        matrix.append({
            "chapter": chapter_id,
            "depends_on": depends,
            "feeds_into": feeds,
        })

    return {"chains": chains, "dependency_matrix": matrix}


def parse_continuity_log() -> dict:
    """Parse chapter coverage count and promises from continuity-log.md."""
    path = ROOT / "review/continuity-log.md"
    if not path.exists():
        return {"chapters_logged": 0, "promises": []}
    text = path.read_text(encoding="utf-8")

    chapters_logged = len(re.findall(r"^### Chapter \d+", text, re.M))

    promises = []
    # Find promises per chapter
    for m in re.finditer(
        r"### Chapter (\d+).*?\*\*Promises to reader:\*\*\s*(.+?)(?=\n---|\n### |\Z)",
        text,
        re.S,
    ):
        chapter = int(m.group(1))
        raw = m.group(2).strip()
        for line in raw.split("\n"):
            line = line.strip()
            if not line or line.startswith("---"):
                break
            # Remove markdown bold/italic if present
            q = re.sub(r"[*_]", "", line).strip()
            if q:
                promises.append({"chapter": chapter, "question": q})

    return {"chapters_logged": chapters_logged, "promises": promises}


def parse_revision_queue() -> dict:
    """Count open/closed items in revision-queue.md."""
    path = ROOT / "review/revision-queue.md"
    if not path.exists():
        return {"open": 0, "closed": 0}
    text = path.read_text(encoding="utf-8")
    # Strip fenced code blocks so template examples aren't counted
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    open_count = len(re.findall(r"^- \[ \]", text, re.M))
    closed_count = len(re.findall(r"^- \[x\]", text, re.M | re.I))
    return {"open": open_count, "closed": closed_count}


def count_drafted_chapters() -> int:
    """Count HTML files in manuscript/."""
    return len(list((ROOT / "manuscript").glob("**/*.html")))


# ── Docs index ────────────────────────────────────────────────────

CATEGORY_MAP = {
    "bible": "bible",
    "outline": "outline",
    "review": "review",
    "style": "style",
    "schema": "schema",
    "agents": "agents",
    "translations": "translations",
    "assets": "assets",
}


def categorize(rel_path: str) -> str:
    """Assign a category based on the first path component."""
    first = rel_path.split("/")[0]
    return CATEGORY_MAP.get(first, "root")


def strip_md_inline(text: str) -> str:
    """Remove markdown bold/italic markers and link syntax."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)   # **bold**
    text = re.sub(r"\*(.+?)\*", r"\1", text)         # *italic*
    text = re.sub(r"__(.+?)__", r"\1", text)          # __bold__
    text = re.sub(r"_(.+?)_", r"\1", text)            # _italic_
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)  # [text](url)
    text = re.sub(r"`([^`]+)`", r"\1", text)          # `code`
    return text.strip()


def first_meaningful_line(path: Path) -> str:
    """Return first non-empty, non-heading, non-metadata line."""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
    except Exception:
        return ""
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        if stripped.startswith(">"):
            # Use blockquote content as synopsis
            return strip_md_inline(stripped.lstrip("> ").strip())[:120]
        if stripped.startswith("---"):
            continue
        if stripped.startswith("```"):
            continue
        return strip_md_inline(stripped)[:120]
    return ""


def build_docs_index() -> list[dict]:
    """Index all .md files under ROOT with metadata."""
    docs = []
    skip_dirs = {"manuscript", "meta", "translations", ".venv"}

    for md in sorted(ROOT.rglob("*.md")):
        rel = str(md.relative_to(ROOT))
        parts = rel.split("/")
        # Skip any path component that starts with a dot or is in skip_dirs
        if any(p.startswith(".") or p in skip_dirs for p in parts[:-1]):
            continue
        top_dir = parts[0]
        if top_dir in skip_dirs:
            continue
        stat = md.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
        category = categorize(rel)
        name = md.stem
        synopsis = first_meaningful_line(md)

        try:
            content = md.read_text(encoding="utf-8", errors="replace")
        except Exception:
            content = ""

        docs.append({
            "category": category,
            "name": name,
            "path": rel,
            "mtime_iso": mtime,
            "synopsis": synopsis,
            "content": content,
        })

    return docs


# ── Mermaid diagram builders ─────────────────────────────────────

def build_mermaid_pipeline() -> str:
    """Pipeline diagram: draft -> html -> site."""
    return (
        "graph LR\n"
        "  draft[\".draft.md\"] --> convert[\"convert.py\"]\n"
        "  convert --> html[\".html chapters\"]\n"
        "  html --> publish[\"publish_book.py\"]\n"
        "  publish --> site[\"site/books/slug/\"]\n"
        "  site --> cf[\"Cloudflare Pages\"]\n"
        "  storyos_yaml[\"storyos.yaml\"] --> build_storyos[\"build_storyos.py\"]\n"
        "  entities[\"entities.yaml\"] --> build_storyos\n"
        "  cards[\"chapter-cards.yaml\"] --> build_storyos\n"
        "  build_storyos --> json[\"storyos.json\"]\n"
        "  build_storyos --> md[\"storyos.md\"]"
    )


def build_mermaid_arc_map(arcs: list[dict], chapters: list[dict]) -> str:
    """Arc map: arcs as subgraphs with chapter nodes."""
    lines = ["graph TD"]
    for arc in arcs:
        arc_id = arc["id"]
        title = arc["title"]
        lo, hi = arc["chapter_range"]
        lines.append(f'  subgraph arc{arc_id}["Arc {arc_id}: {title}"]')
        for ch in chapters:
            cn = ch["chapter"]
            if lo <= cn <= hi:
                pov = ch.get("pov", "?")
                lines.append(f'    ch{cn}["Ch {cn}: {pov}"]')
        lines.append("  end")
        if arc_id > 1:
            prev_hi = arcs[arc_id - 2]["chapter_range"][1]
            lines.append(f"  ch{prev_hi} --> ch{lo}")
    return "\n".join(lines)


def _mermaid_node_id(raw_id: str) -> str:
    """Convert '1.3' or 'BACKSTORY ~2150' to a valid Mermaid node id."""
    if raw_id.startswith("BACKSTORY"):
        return "n_back_" + re.sub(r"\W+", "_", raw_id).strip("_")
    return "n" + raw_id.replace(".", "_")


def _truncate(text: str, maxlen: int = 40) -> str:
    if len(text) <= maxlen:
        return text
    return text[: maxlen - 3] + "..."


def build_mermaid_butterfly(graph: dict) -> str:
    """Causal chains as a Mermaid flowchart with subgraphs per chain."""
    lines = ["graph TD"]
    for chain_id, chain in sorted(graph.get("chains", {}).items()):
        title = chain["title"]
        lines.append(f'  subgraph {chain_id}["{chain_id}: {title}"]')
        for node in chain.get("nodes", []):
            nid = _mermaid_node_id(node["id"])
            label = _truncate(node["label"])
            # Escape quotes in label
            label = label.replace('"', "'")
            lines.append(f'    {nid}["{node["id"]}: {label}"]')
        lines.append("  end")

    # Edges (outside subgraphs so cross-chain edges work)
    for chain_id, chain in sorted(graph.get("chains", {}).items()):
        for edge in chain.get("edges", []):
            f = _mermaid_node_id(edge["from"])
            t = _mermaid_node_id(edge["to"])
            lines.append(f"  {f} --> {t}")

    return "\n".join(lines)


# ── Assembly ──────────────────────────────────────────────────────

def assemble_json(
    config: dict,
    entities: dict,
    chapters: list[dict],
    book_meta: dict,
    arcs_md: list[dict],
    graph: dict,
    continuity: dict,
    revision: dict,
    drafted: int,
    docs: list[dict],
) -> dict:
    """Assemble the full JSON payload."""
    now = datetime.now(tz=timezone.utc).isoformat()

    meta = config.get("meta", {})
    book = config.get("book", {})
    # Merge book.yaml values
    book.setdefault("title", book_meta.get("title", ""))
    book.setdefault("subtitle", book_meta.get("subtitle", ""))

    arcs = config.get("arcs", [])
    threads = config.get("threads", [])
    promises = config.get("promises", [])
    pins = config.get("dashboard_pins", [])

    mermaid_arcs = build_mermaid_arc_map(arcs, chapters)
    mermaid_butterfly = build_mermaid_butterfly(graph)
    mermaid_pipeline = build_mermaid_pipeline()

    return {
        "generated_at": now,
        "meta": meta,
        "book": book,
        "arcs": arcs,
        "threads": threads,
        "promises": promises,
        "dashboard_pins": pins,
        "stats": {
            "total_chapters": 40,
            "chapters_drafted": drafted,
            "chapters_with_html": drafted,
            "continuity_chapters_logged": continuity["chapters_logged"],
            "revision_queue_open": revision["open"],
            "revision_queue_closed": revision["closed"],
        },
        "entities": entities.get("entities", {}),
        "do_not_translate_tokens": entities.get("do_not_translate_tokens", []),
        "chapters": chapters,
        "butterfly_graph": graph,
        "docs_index": docs,
        "mermaid": {
            "pipeline": mermaid_pipeline,
            "arc_map": mermaid_arcs,
            "butterfly": mermaid_butterfly,
        },
    }


# ── Markdown renderer ────────────────────────────────────────────

def render_markdown(data: dict) -> str:
    """Render the JSON payload as a scannable Markdown dashboard."""
    lines: list[str] = []

    book = data["book"]
    lines.append(f"# {book.get('title', 'Untitled')}")
    if book.get("subtitle"):
        lines.append(f"*{book['subtitle']}*")
    lines.append("")
    if book.get("working_title"):
        lines.append(f"**Working title:** {book['working_title']}")
    if book.get("core_question"):
        lines.append(f"**Core question:** {book['core_question']}")
    lines.append(f"\n*Generated {data['generated_at'][:19]}Z*")
    lines.append("")

    # At a Glance
    s = data["stats"]
    lines.append("---")
    lines.append("## At a Glance")
    lines.append("")
    lines.append(f"- **Chapters planned:** {s['total_chapters']}")
    lines.append(f"- **Chapters drafted (HTML):** {s['chapters_drafted']}")
    lines.append(f"- **Continuity log coverage:** {s['continuity_chapters_logged']}/{s['total_chapters']} chapters")
    lines.append(f"- **Revision queue:** {s['revision_queue_open']} open / {s['revision_queue_closed']} closed")
    lines.append("")

    # Dashboard Pins
    pins = data.get("dashboard_pins", [])
    if pins:
        lines.append("## Dashboard Pins")
        lines.append("")
        for pin in pins:
            lines.append(f"- {pin}")
        lines.append("")

    # Docs Index
    lines.append("---")
    lines.append("## Docs Index")
    lines.append("")
    docs = data.get("docs_index", [])
    by_cat: dict[str, list[dict]] = {}
    for d in docs:
        by_cat.setdefault(d["category"], []).append(d)
    cat_order = ["root", "bible", "outline", "review", "style", "schema", "agents", "assets"]
    for cat in cat_order:
        items = by_cat.get(cat, [])
        if not items:
            continue
        lines.append(f"### {cat.title()}")
        lines.append("")
        lines.append("| File | Synopsis | Last Modified |")
        lines.append("|------|----------|---------------|")
        for item in sorted(items, key=lambda x: x["path"]):
            synopsis = item["synopsis"][:80] if item["synopsis"] else ""
            mtime = item["mtime_iso"][:10]
            lines.append(f"| `{item['path']}` | {synopsis} | {mtime} |")
        lines.append("")

    # Arcs and Chapters
    lines.append("---")
    lines.append("## Arcs")
    lines.append("")
    for arc in data.get("arcs", []):
        lo, hi = arc["chapter_range"]
        lines.append(f"**Arc {arc['id']}: {arc['title']}** (Ch {lo}--{hi}) -- {arc.get('purpose', '')}")
    lines.append("")

    lines.append("## Chapter Table")
    lines.append("")
    lines.append("| Ch | Title | POV | World | Location | Timeline | Hook |")
    lines.append("|----|-------|-----|-------|----------|----------|------|")
    for ch in data.get("chapters", []):
        hook = (ch.get("hook") or "")[:60]
        lines.append(
            f"| {ch['chapter']} "
            f"| {ch.get('title', '')} "
            f"| {ch.get('pov', '')} "
            f"| {ch.get('world', '')} "
            f"| {ch.get('location', '')} "
            f"| {ch.get('timeline', '')} "
            f"| {hook} |"
        )
    lines.append("")

    # Entities
    lines.append("---")
    lines.append("## Entities")
    lines.append("")
    entities = data.get("entities", {})
    for etype in ["characters", "places", "concepts"]:
        items = entities.get(etype, [])
        if not items:
            continue
        lines.append(f"### {etype.title()}")
        lines.append("")
        for e in items:
            notes = "; ".join(e.get("notes", []))
            culture = e.get("culture", "")
            lines.append(f"- **{e.get('name', e.get('id', ''))}** ({culture}) {notes}")
        lines.append("")

    dnt = data.get("do_not_translate_tokens", [])
    if dnt:
        lines.append("### Do Not Translate")
        lines.append("")
        lines.append(", ".join(f"`{t}`" for t in dnt))
        lines.append("")

    # Threads & Promises
    lines.append("---")
    lines.append("## Threads")
    lines.append("")
    for t in data.get("threads", []):
        status_icon = {"open": "🔵", "closed": "✅", "dormant": "💤"}.get(t.get("status", ""), "")
        lines.append(
            f"- {status_icon} **{t['title']}** ({t['status']}) "
            f"Ch {t.get('introduced_in_chapter', '?')}--{t.get('last_touched_chapter', '?')}"
        )
        if t.get("next_action"):
            lines.append(f"  - Next: {t['next_action']}")
    lines.append("")

    lines.append("## Promises")
    lines.append("")
    lines.append("| Status | Question | Introduced | Payoff Target |")
    lines.append("|--------|----------|------------|---------------|")
    for p in data.get("promises", []):
        status = "✅" if p.get("status") == "closed" else "🔵"
        lines.append(
            f"| {status} | {p.get('question', '')} "
            f"| Ch {p.get('introduced_in_chapter', '?')} "
            f"| Ch {p.get('payoff_target_chapter', '?')} |"
        )
    lines.append("")

    # Diagrams
    lines.append("---")
    lines.append("## Diagrams")
    lines.append("")
    mermaid = data.get("mermaid", {})

    lines.append("### Pipeline")
    lines.append("")
    lines.append("```mermaid")
    lines.append(mermaid.get("pipeline", ""))
    lines.append("```")
    lines.append("")

    lines.append("### Arc Map")
    lines.append("")
    lines.append("```mermaid")
    lines.append(mermaid.get("arc_map", ""))
    lines.append("```")
    lines.append("")

    lines.append("### Butterfly Graph")
    lines.append("")
    lines.append("```mermaid")
    lines.append(mermaid.get("butterfly", ""))
    lines.append("```")
    lines.append("")

    return "\n".join(lines)


# ── Validation ────────────────────────────────────────────────────

def validate(config: dict, chapters: list[dict]) -> list[str]:
    """Return a list of validation error messages."""
    errors: list[str] = []

    # Check storyos.yaml structure
    if "meta" not in config:
        errors.append("storyos.yaml: missing 'meta' key")
    if "book" not in config:
        errors.append("storyos.yaml: missing 'book' key")
    if "arcs" not in config:
        errors.append("storyos.yaml: missing 'arcs' key")

    # Check arc coverage
    arcs = config.get("arcs", [])
    covered = set()
    for arc in arcs:
        lo, hi = arc.get("chapter_range", [0, 0])
        for c in range(lo, hi + 1):
            covered.add(c)
    for c in range(1, 41):
        if c not in covered:
            errors.append(f"Chapter {c} not covered by any arc in storyos.yaml")

    # Check chapter cards exist
    if len(chapters) != 40:
        errors.append(f"Expected 40 chapters in chapter-cards.yaml, found {len(chapters)}")

    # Check threads have valid statuses
    for t in config.get("threads", []):
        if t.get("status") not in ("open", "closed", "dormant"):
            errors.append(f"Thread '{t.get('id')}' has invalid status: {t.get('status')}")

    # Check promises have valid statuses
    for p in config.get("promises", []):
        if p.get("status") not in ("open", "closed"):
            errors.append(f"Promise '{p.get('id')}' has invalid status: {p.get('status')}")

    # Check required source files exist
    required = [
        "schema/storyos.yaml",
        "schema/entities.yaml",
        "schema/chapter-cards.yaml",
        "book.yaml",
    ]
    for f in required:
        if not (ROOT / f).exists():
            errors.append(f"Required file missing: {f}")

    return errors


# ── CLI entry ─────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build StoryOS metadata hub")
    parser.add_argument("--check", action="store_true", help="Validate only, do not write files")
    args = parser.parse_args(argv)

    # Load all sources
    config = load_storyos()
    entities = load_entities()
    chapters = load_chapters()
    book_meta = load_book_meta()

    # Validate
    errors = validate(config, chapters)
    if errors:
        for e in errors:
            print(f"  ERROR: {e}")
        if args.check:
            return 1

    if args.check:
        print("Validation passed.")
        return 0

    # Parse supplemental sources
    arcs_md = parse_arcs_md()
    graph = parse_butterfly_graph()
    continuity = parse_continuity_log()
    revision = parse_revision_queue()
    drafted = count_drafted_chapters()
    docs = build_docs_index()

    # Assemble
    payload = assemble_json(
        config, entities, chapters, book_meta,
        arcs_md, graph, continuity, revision, drafted, docs,
    )

    # Write JSON
    out_dir = ROOT / "meta"
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "storyos.json"
    json_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {json_path.relative_to(ROOT)}")

    # Write Markdown
    md_path = out_dir / "storyos.md"
    md_text = render_markdown(payload)
    md_path.write_text(md_text, encoding="utf-8")
    print(f"Wrote {md_path.relative_to(ROOT)}")

    print(f"  {len(chapters)} chapters, {len(docs)} docs indexed, {drafted} HTML files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
