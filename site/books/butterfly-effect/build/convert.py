#!/usr/bin/env python3
"""Convert book .draft.md files to .html chapters + table of contents."""

import re
import os
import html
import yaml

# Arc metadata
ARCS = {
    1: "The Silence",
    2: "The Signal",
    3: "The Crossing",
    4: "The Stranger",
    5: "The Mirror",
    6: "The Return",
    7: "The Choice",
}

# Chapter metadata: (arc, number, title, pov, location, timeline)
CHAPTERS = []

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANUSCRIPT = os.path.join(BASE, "manuscript")
BUILD = os.path.join(BASE, "build")
STYLE_REL = "../../style/novel.css"
INDEX_REL = "../../index.html"
SIGIL_REL = "../../assets/sigils"


def load_book_config():
    """Load per-book metadata from `book.yaml` (optional)."""
    defaults = {
        "title": os.path.basename(BASE) or "Untitled",
        "subtitle": "A Novel",
        "arcade_href": "/",
        "arcade_label": "All books",
        "home_href": "https://too.foo/",
        "home_label": "too.foo",
    }
    p = os.path.join(BASE, "book.yaml")
    if not os.path.isfile(p):
        return defaults
    try:
        with open(p, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        if not isinstance(cfg, dict):
            return defaults
        out = defaults.copy()
        out.update({k: v for k, v in cfg.items() if v is not None})
        return out
    except Exception:
        return defaults


BOOK = load_book_config()
BOOK_TITLE = str(BOOK.get("title") or "")
BOOK_SUBTITLE = str(BOOK.get("subtitle") or "")
ARCADE_HREF = str(BOOK.get("arcade_href") or "/")
ARCADE_LABEL = str(BOOK.get("arcade_label") or "All books")
HOME_HREF = str(BOOK.get("home_href") or "https://too.foo/")
HOME_LABEL = str(BOOK.get("home_label") or "too.foo")


def load_sigil_map():
    try:
        p = os.path.join(BASE, "style", "chapter-svg-themes.yaml")
        with open(p, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        out = {}
        for ch in cfg.get("chapters", []) or []:
            if not isinstance(ch, dict):
                continue
            num = int(ch.get("chapter"))
            out[num] = {"id": ch.get("id", ""), "alt": ch.get("alt", "")}
        return out
    except Exception:
        return {}


SIGIL_MAP = load_sigil_map()


def sigil_img(chapter_num, rel_base):
    sig = SIGIL_MAP.get(chapter_num)
    if not sig or not sig.get("id"):
        return ""
    src = f"{rel_base}/{sig['id']}.svg"
    alt = html.escape(sig.get("alt", "") or "")
    return f'<img class="sigil" src="{src}" alt="{alt}" loading="lazy" decoding="async">'


def parse_draft(filepath):
    """Parse a .draft.md file and extract metadata + prose."""
    with open(filepath, "r") as f:
        content = f.read()

    # Extract title from first line: # Chapter N: Title
    title_match = re.match(r"^# Chapter (\d+):\s*(.+)$", content, re.MULTILINE)
    if not title_match:
        return None
    chapter_num = int(title_match.group(1))
    chapter_title = title_match.group(2).strip()

    # Extract metadata from HTML comment
    meta_match = re.search(
        r"<!--\s*Arc:\s*(\d+)\s*\|\s*POV:\s*(.+?)\s*\|\s*Location:\s*(.+?)\s*\|\s*Timeline:\s*(.+?)\s*-->",
        content,
    )
    if meta_match:
        arc_num = int(meta_match.group(1))
        pov = meta_match.group(2).strip()
        location = meta_match.group(3).strip()
        timeline = meta_match.group(4).strip()
    else:
        arc_num = 1
        pov = "Unknown"
        location = "Unknown"
        timeline = "Unknown"

    # Strip everything before first non-comment, non-header prose
    # Remove title line, metadata comments, beat comments, continuity notes
    lines = content.split("\n")
    prose_lines = []
    in_continuity = False
    for line in lines:
        # Skip title
        if re.match(r"^# Chapter \d+:", line):
            continue
        # Skip HTML comments (single-line)
        if re.match(r"^\s*<!--.*-->\s*$", line):
            continue
        # Skip multi-line HTML comment start
        if re.match(r"^\s*<!--", line) and "-->" not in line:
            in_continuity = True
            continue
        # Inside multi-line comment
        if in_continuity:
            if "-->" in line:
                in_continuity = False
            continue
        # Skip word count target lines
        if re.match(r"^\s*<!--\s*Word count", line, re.IGNORECASE):
            continue
        prose_lines.append(line)

    prose = "\n".join(prose_lines).strip()

    # Remove trailing --- and anything after (continuity notes)
    prose = re.sub(r"\n---\s*$", "", prose)

    return {
        "chapter_num": chapter_num,
        "chapter_title": chapter_title,
        "arc_num": arc_num,
        "pov": pov,
        "location": location,
        "timeline": timeline,
        "prose": prose,
    }


def prose_to_html(prose):
    """Convert markdown prose to HTML paragraphs."""
    # Split on scene breaks (--- or ***)
    # First, handle scene breaks
    prose = re.sub(r"\n\s*\*\s*\*\s*\*\s*\n", "\n<SCENE_BREAK>\n", prose)
    prose = re.sub(r"\n---\n", "\n<SCENE_BREAK>\n", prose)

    # Handle blockquotes (> lines) - often used for pidgin/translation
    lines = prose.split("\n")
    result_lines = []
    in_blockquote = False
    for line in lines:
        if line.startswith("> "):
            if not in_blockquote:
                result_lines.append("<BLOCKQUOTE_START>")
                in_blockquote = True
            result_lines.append(line[2:])
        else:
            if in_blockquote:
                result_lines.append("<BLOCKQUOTE_END>")
                in_blockquote = False
            result_lines.append(line)
    if in_blockquote:
        result_lines.append("<BLOCKQUOTE_END>")
    prose = "\n".join(result_lines)

    # Split into paragraphs (double newline)
    paragraphs = re.split(r"\n\s*\n", prose)

    html_parts = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if para == "<SCENE_BREAK>":
            html_parts.append('    <hr class="scene-break">')
            continue

        # Handle blockquotes
        if "<BLOCKQUOTE_START>" in para:
            para = para.replace("<BLOCKQUOTE_START>", "").strip()
            if "<BLOCKQUOTE_END>" in para:
                para = para.replace("<BLOCKQUOTE_END>", "").strip()
            bq_lines = para.split("\n")
            bq_html = "\n".join(
                f"      <p>{process_inline(l.strip())}</p>" for l in bq_lines if l.strip()
            )
            html_parts.append(f"    <blockquote>\n{bq_html}\n    </blockquote>")
            continue

        if "<BLOCKQUOTE_END>" in para:
            para = para.replace("<BLOCKQUOTE_END>", "").strip()

        if not para:
            continue

        # Convert markdown italics to <em>
        para = process_inline(para)
        html_parts.append(f"    <p>{para}</p>")

    return "\n".join(html_parts)


def process_inline(text):
    """Process inline markdown: *italic*, **bold**."""
    # Escape HTML entities first
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")

    # Bold: **text**
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # Italic: *text*
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)

    return text


def generate_chapter_html(data, prev_href, next_href):
    """Generate the full HTML for a chapter."""
    arc_title = ARCS.get(data["arc_num"], "Unknown")
    prose_html = prose_to_html(data["prose"])
    sigil_html = sigil_img(data["chapter_num"], SIGIL_REL)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(BOOK_TITLE)} — Chapter {data['chapter_num']}: {html.escape(data['chapter_title'])}</title>
  <link rel="stylesheet" href="{STYLE_REL}">
</head>
<body>
  <div class="progress-bar" aria-hidden="true"></div>
  <nav class="chapter-nav">
    <a href="{prev_href}">← Previous</a>
    <a href="{INDEX_REL}">Contents</a>
    <a href="{next_href}">Next →</a>
  </nav>
  <header>
    <div class="chapter-sigil">{sigil_html}</div>
    <p class="arc-label">Arc {data['arc_num']}: {html.escape(arc_title)}</p>
    <h1>Chapter {data['chapter_num']}<br><span class="chapter-title">{html.escape(data['chapter_title'])}</span></h1>
    <p class="chapter-meta">{html.escape(data['pov'])} · {html.escape(data['location'])} · {html.escape(data['timeline'])}</p>
  </header>
  <article class="chapter-body">
{prose_html}
  </article>
  <nav class="chapter-nav bottom">
    <a href="{prev_href}">← Previous</a>
    <a href="{INDEX_REL}">Contents</a>
    <a href="{next_href}">Next →</a>
  </nav>
  <script>
    (() => {{
      const bar = document.querySelector('.progress-bar');
      if (!bar) return;
      const update = () => {{
        const doc = document.documentElement;
        const y = doc.scrollTop || document.body.scrollTop || 0;
        const h = (doc.scrollHeight || 0) - (doc.clientHeight || 0);
        const p = h > 0 ? Math.min(100, Math.max(0, (y / h) * 100)) : 0;
        bar.style.width = p.toFixed(3) + '%';
      }};
      document.addEventListener('scroll', update, {{ passive: true }});
      update();
    }})();
  </script>
</body>
</html>
"""


def generate_index(chapters, *, style_href, manuscript_prefix, sigil_rel_base):
    """Generate index.html table of contents."""
    arc_groups = {}
    for ch in chapters:
        arc = ch["arc_num"]
        if arc not in arc_groups:
            arc_groups[arc] = []
        arc_groups[arc].append(ch)

    groups_html = []
    for arc_num in sorted(arc_groups.keys()):
        arc_title = ARCS.get(arc_num, "Unknown")
        links = []
        for ch in arc_groups[arc_num]:
            num_str = f"{ch['chapter_num']:02d}"
            href = f"{manuscript_prefix}/arc-{arc_num}/chapter-{num_str}.html"
            sigil_html = sigil_img(ch["chapter_num"], sigil_rel_base)
            links.append(
                f'''    <a class="chapter-link" href="{href}">
      <span class="chapter-sigil">{sigil_html}</span>
      <span class="chapter-number">{ch["chapter_num"]}.</span>
      <span class="chapter-text">
        <span class="chapter-title">{html.escape(ch["chapter_title"])}</span>
        <span class="chapter-sub">{html.escape(ch["pov"])} · {html.escape(ch["location"])}</span>
      </span>
    </a>'''
            )
        groups_html.append(
            f"""  <div class="arc-group">
    <h2>Arc {arc_num}: {html.escape(arc_title)}</h2>
{chr(10).join(links)}
  </div>"""
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(BOOK_TITLE)} — Table of Contents</title>
  <link rel="stylesheet" href="{style_href}">
</head>
<body>
  <nav class="toc-nav" aria-label="Book navigation">
    <a class="toc-pill" href="{html.escape(ARCADE_HREF)}">← {html.escape(ARCADE_LABEL)}</a>
    <a class="toc-pill" href="{html.escape(HOME_HREF)}" target="_blank" rel="noopener noreferrer">{html.escape(HOME_LABEL)} ↗</a>
  </nav>
  <div class="index-header">
    <h1>{html.escape(BOOK_TITLE)}</h1>
    <p class="subtitle">{html.escape(BOOK_SUBTITLE)}</p>
  </div>
{chr(10).join(groups_html)}
</body>
</html>
"""


def main():
    chapters = []

    # Collect all draft files
    for arc_num in range(1, 8):
        arc_dir = os.path.join(MANUSCRIPT, f"arc-{arc_num}")
        if not os.path.isdir(arc_dir):
            continue
        for fname in sorted(os.listdir(arc_dir)):
            if fname.endswith(".draft.md"):
                filepath = os.path.join(arc_dir, fname)
                data = parse_draft(filepath)
                if data:
                    chapters.append(data)

    chapters.sort(key=lambda x: x["chapter_num"])
    print(f"Found {len(chapters)} chapters")

    # Generate HTML for each chapter
    for i, ch in enumerate(chapters):
        arc_dir = os.path.join(MANUSCRIPT, f"arc-{ch['arc_num']}")
        num_str = f"{ch['chapter_num']:02d}"
        html_path = os.path.join(arc_dir, f"chapter-{num_str}.html")

        # Navigation links
        if i > 0:
            prev_ch = chapters[i - 1]
            prev_num = f"{prev_ch['chapter_num']:02d}"
            prev_href = f"../arc-{prev_ch['arc_num']}/chapter-{prev_num}.html"
        else:
            prev_href = INDEX_REL

        if i < len(chapters) - 1:
            next_ch = chapters[i + 1]
            next_num = f"{next_ch['chapter_num']:02d}"
            next_href = f"../arc-{next_ch['arc_num']}/chapter-{next_num}.html"
        else:
            next_href = INDEX_REL

        chapter_html = generate_chapter_html(ch, prev_href, next_href)
        with open(html_path, "w") as f:
            f.write(chapter_html)
        print(f"  ✓ Chapter {ch['chapter_num']}: {ch['chapter_title']} → {html_path}")

    os.makedirs(BUILD, exist_ok=True)

    # Generate index (book root, used for deployment)
    index_root_path = os.path.join(BASE, "index.html")
    index_root_html = generate_index(
        chapters,
        style_href="style/novel.css",
        manuscript_prefix="manuscript",
        sigil_rel_base="assets/sigils",
    )
    with open(index_root_path, "w") as f:
        f.write(index_root_html)
    print(f"  ✓ Index → {index_root_path}")

    # Generate legacy index (build/), kept for backwards compatibility
    index_build_path = os.path.join(BUILD, "index.html")
    index_build_html = generate_index(
        chapters,
        style_href="../style/novel.css",
        manuscript_prefix="../manuscript",
        sigil_rel_base="../assets/sigils",
    )
    with open(index_build_path, "w") as f:
        f.write(index_build_html)
    print(f"  ✓ Index (legacy) → {index_build_path}")
    print(f"\nDone. {len(chapters)} chapters converted.")


if __name__ == "__main__":
    main()
