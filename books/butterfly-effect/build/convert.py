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
ILLUST_REL = "../../assets/illustrations"
DIAGRAM_REL = "../../assets/diagrams"

# Illustration marker regex: <!-- @illust full|thumb|link: id | alt -->
ILLUST_RE = re.compile(
    r"<!--\s*@illust\s+(full|thumb|link):\s*([a-z0-9_-]+)\s*\|\s*(.+?)\s*-->"
)

# Diagram marker regex: <!-- @diagram full|thumb|link: id | alt -->
DIAGRAM_RE = re.compile(
    r"<!--\s*@diagram\s+(full|thumb|link):\s*([a-z0-9_-]+)\s*\|\s*(.+?)\s*-->"
)

ILLUST_WIDTHS = [480, 768, 1200]

def render_inline_markdown(text: str) -> str:
    """Escape HTML but allow simple markdown emphasis in link text."""
    s = html.escape(text)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
    return s


def strip_inline_markdown(text: str) -> str:
    """Best-effort plain-text for aria-labels/tooltips."""
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    s = re.sub(r"\*(.+?)\*", r"\1", s)
    return s


def picture_element(illust_id, alt, rel_base, cls="", sizes="100vw"):
    """Generate a <picture> element with AVIF/WebP sources at multiple widths."""
    avif_srcset = ", ".join(
        f"{rel_base}/{illust_id}-{w}w.avif {w}w" for w in ILLUST_WIDTHS
    )
    webp_srcset = ", ".join(
        f"{rel_base}/{illust_id}-{w}w.webp {w}w" for w in ILLUST_WIDTHS
    )
    fallback_src = f"{rel_base}/{illust_id}-{ILLUST_WIDTHS[-1]}w.webp"
    alt_esc = html.escape(alt)
    cls_attr = f' class="{cls}"' if cls else ""
    return (
        f'<picture>'
        f'<source type="image/avif" srcset="{avif_srcset}" sizes="{sizes}">'
        f'<source type="image/webp" srcset="{webp_srcset}" sizes="{sizes}">'
        f'<img{cls_attr} src="{fallback_src}" alt="{alt_esc}" loading="lazy" decoding="async">'
        f'</picture>'
    )


def illust_full_html(illust_id, caption, rel_base):
    """Full-width illustration figure."""
    pic = picture_element(illust_id, caption, rel_base, sizes="(min-width: 900px) 82ch, 100vw")
    full_src = f"{rel_base}/{illust_id}-{ILLUST_WIDTHS[-1]}w.webp"
    cap_esc = html.escape(caption)
    return (
        f'    <figure class="illust-full" data-illust="{html.escape(illust_id)}">'
        f'<a class="illust-zoom" href="{full_src}" data-full="{full_src}" aria-label="View: {cap_esc}">'
        f'{pic}</a><figcaption>{cap_esc}</figcaption></figure>'
    )


def illust_thumb_html(illust_id, alt, rel_base):
    """Inline thumbnail that expands on click."""
    thumb_src = f"{rel_base}/{illust_id}-{ILLUST_WIDTHS[0]}w.webp"
    full_src = f"{rel_base}/{illust_id}-{ILLUST_WIDTHS[-1]}w.webp"
    alt_esc = html.escape(alt)
    return (
        f'<a class="illust-thumb" data-illust="{html.escape(illust_id)}" '
        f'data-full="{full_src}" href="{full_src}" aria-label="View: {alt_esc}">'
        f'<img src="{thumb_src}" alt="{alt_esc}" loading="lazy" decoding="async">'
        f'</a>'
    )


def illust_link_html(illust_id, link_text, rel_base):
    """Text that opens an illustration overlay on click."""
    full_src = f"{rel_base}/{illust_id}-{ILLUST_WIDTHS[-1]}w.webp"
    link_html = render_inline_markdown(link_text)
    label = html.escape(strip_inline_markdown(link_text).strip() or "Illustration")
    return (
        f'<a class="illust-link" data-illust="{html.escape(illust_id)}" '
        f'data-full="{full_src}" href="{full_src}" aria-label="View illustration: {label}">'
        f'{link_html}</a>'
    )


def diagram_src(diagram_id: str, rel_base: str) -> str:
    return f"{rel_base}/{diagram_id}.svg"


def diagram_full_html(diagram_id: str, caption: str, rel_base: str) -> str:
    """Full-width SVG diagram figure."""
    src = diagram_src(diagram_id, rel_base)
    cap_esc = html.escape(caption)
    return (
        f'    <figure class="illust-full diagram-full" data-diagram="{html.escape(diagram_id)}">'
        f'<a class="illust-zoom" href="{src}" data-full="{src}" aria-label="View: {cap_esc}">'
        f'<img src="{src}" alt="{cap_esc}" loading="lazy" decoding="async"></a>'
        f'<figcaption>{cap_esc}</figcaption></figure>'
    )


def diagram_thumb_html(diagram_id: str, alt: str, rel_base: str) -> str:
    """Inline SVG thumbnail (click to open)."""
    src = diagram_src(diagram_id, rel_base)
    alt_esc = html.escape(alt)
    return (
        f'<a class="illust-thumb diagram-thumb" data-diagram="{html.escape(diagram_id)}" '
        f'data-full="{src}" href="{src}" aria-label="View: {alt_esc}">'
        f'<img src="{src}" alt="{alt_esc}" loading="lazy" decoding="async">'
        f"</a>"
    )


def diagram_link_html(diagram_id: str, link_text: str, rel_base: str) -> str:
    """Text that opens an SVG diagram overlay on click."""
    src = diagram_src(diagram_id, rel_base)
    link_html = render_inline_markdown(link_text)
    label = html.escape(strip_inline_markdown(link_text).strip() or "Diagram")
    return (
        f'<a class="illust-link diagram-link" data-diagram="{html.escape(diagram_id)}" '
        f'data-full="{src}" href="{src}" aria-label="View diagram: {label}">'
        f"{link_html}</a>"
    )


# POV → world mapping for SVG animation styles
POV_WORLD = {
    "Kael": "continental",
    "Moss": "continental",
    "Sūrya": "antarctic",
    "Sūrya + VEDA": "antarctic",
    "Dual": "dual",
    "Dual + VEDA": "dual",
}


def get_world(pov):
    """Map a POV character to a world animation style."""
    return POV_WORLD.get(pov, "continental")


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


def sigil_img(chapter_num, rel_base, inline=False, world="continental"):
    """Generate sigil markup. When inline=True, embed the SVG directly with animation attrs."""
    sig = SIGIL_MAP.get(chapter_num)
    if not sig or not sig.get("id"):
        return ""
    if inline:
        svg_path = os.path.join(BASE, "assets", "sigils", f"{sig['id']}.svg")
        if os.path.isfile(svg_path):
            with open(svg_path, "r", encoding="utf-8") as f:
                svg_content = f.read().strip()
            # Strip XML declaration if present
            svg_content = re.sub(r"<\?xml[^?]*\?>", "", svg_content).strip()
            # Inject classes and attributes into the <svg> tag
            alt = html.escape(sig.get("alt", "") or "")
            inject = (
                f'class="sigil svg-anim svg-anim-{html.escape(world)}" '
                f'data-anim="draw-on-scroll" role="img" aria-label="{alt}"'
            )
            svg_content = re.sub(r"<svg\b", f"<svg {inject}", svg_content, count=1)
            return svg_content
    # Fallback: external <img> tag (used for TOC)
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
        # Preserve visual markers (they look like comments but carry data)
        if re.match(r"^\s*<!--\s*@(illust|diagram)\s", line):
            prose_lines.append(line)
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

        # Block-level full illustration (standalone paragraph)
        full_match = re.match(
            r"^\s*<!--\s*@illust\s+full:\s*([a-z0-9_-]+)\s*\|\s*(.+?)\s*-->\s*$",
            para,
        )
        if full_match:
            html_parts.append(illust_full_html(full_match.group(1), full_match.group(2).strip(), ILLUST_REL))
            continue

        # Block-level full diagram (standalone paragraph)
        diag_full_match = re.match(
            r"^\s*<!--\s*@diagram\s+full:\s*([a-z0-9_-]+)\s*\|\s*(.+?)\s*-->\s*$",
            para,
        )
        if diag_full_match:
            html_parts.append(
                diagram_full_html(diag_full_match.group(1), diag_full_match.group(2).strip(), DIAGRAM_REL)
            )
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

        # Process inline visuals before HTML escaping
        para = process_visual_markers(para)
        # Convert markdown italics to <em>
        para = process_inline(para)
        html_parts.append(f"    <p>{para}</p>")

    return "\n".join(html_parts)


def process_visual_markers(text):
    """Replace inline @illust/@diagram thumb/link markers with HTML before general escaping."""
    def _replace_diag(m):
        kind, diagram_id, caption = m.group(1), m.group(2), m.group(3).strip()
        if kind == "thumb":
            return diagram_thumb_html(diagram_id, caption, DIAGRAM_REL)
        elif kind == "link":
            return diagram_link_html(diagram_id, caption, DIAGRAM_REL)
        # full markers handled at block level; pass through if misplaced inline
        return m.group(0)

    def _replace_illust(m):
        kind, illust_id, caption = m.group(1), m.group(2), m.group(3).strip()
        if kind == "thumb":
            return illust_thumb_html(illust_id, caption, ILLUST_REL)
        elif kind == "link":
            return illust_link_html(illust_id, caption, ILLUST_REL)
        # full markers handled at block level; pass through if misplaced inline
        return m.group(0)

    text = DIAGRAM_RE.sub(_replace_diag, text)
    text = ILLUST_RE.sub(_replace_illust, text)
    return text


def process_inline(text):
    """Process inline markdown: *italic*, **bold**.

    Illustration HTML (from process_illustrations) is protected from escaping
    by temporarily replacing it with placeholders.
    """
    # Protect existing HTML tags (from illustration processing) from escaping
    protected = []

    def _protect(m):
        protected.append(m.group(0))
        return f"\x00PROTECT{len(protected) - 1}\x00"

    text = re.sub(r"<[^>]+>", _protect, text)

    # Escape HTML entities in prose text
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")

    # Bold: **text**
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # Italic: *text*
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)

    # Restore protected HTML
    for i, tag in enumerate(protected):
        text = text.replace(f"\x00PROTECT{i}\x00", tag)

    return text


def generate_chapter_html(data, prev_href, next_href):
    """Generate the full HTML for a chapter."""
    arc_title = ARCS.get(data["arc_num"], "Unknown")
    prose_html = prose_to_html(data["prose"])
    world = get_world(data["pov"])
    sigil_html = sigil_img(data["chapter_num"], SIGIL_REL, inline=True, world=world)

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
      /* Progress bar */
      const bar = document.querySelector('.progress-bar');
      if (bar) {{
        const update = () => {{
          const doc = document.documentElement;
          const y = doc.scrollTop || document.body.scrollTop || 0;
          const h = (doc.scrollHeight || 0) - (doc.clientHeight || 0);
          const p = h > 0 ? Math.min(100, Math.max(0, (y / h) * 100)) : 0;
          bar.style.width = p.toFixed(3) + '%';
        }};
        document.addEventListener('scroll', update, {{ passive: true }});
        update();
      }}

      /* SVG draw-on-scroll animation */
      const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (!reduced) {{
        document.querySelectorAll('[data-anim="draw-on-scroll"]').forEach(svg => {{
          const els = svg.querySelectorAll('path, line, circle, polyline, polygon');
          els.forEach(el => {{
            const len = el.getTotalLength ? el.getTotalLength() : 0;
            if (len) {{
              el.style.strokeDasharray = len;
              el.style.strokeDashoffset = len;
            }}
          }});
          const io = new IntersectionObserver(entries => {{
            entries.forEach(e => {{
              if (e.isIntersecting) {{
                svg.classList.add('svg-anim-active');
                io.unobserve(svg);
              }}
            }});
          }}, {{ threshold: 0.3 }});
          io.observe(svg);
        }});
      }}

      /* Lightbox for illustration thumbnails and links */
      function openOverlay(src, alt) {{
        const existing = document.querySelector('.illust-overlay');
        if (existing) existing.remove();
        const ov = document.createElement('div');
        ov.className = 'illust-overlay';
        ov.setAttribute('role', 'dialog');
        ov.setAttribute('aria-label', alt || 'Illustration');
        const img = document.createElement('img');
        img.src = src;
        img.alt = alt || '';
        img.decoding = 'async';
        ov.appendChild(img);
        ov.addEventListener('click', () => ov.remove());
        document.body.appendChild(ov);
      }}
      function closeOverlay(e) {{
        if (e.key === 'Escape') {{
          const ov = document.querySelector('.illust-overlay');
          if (ov) ov.remove();
        }}
      }}
      document.addEventListener('keydown', closeOverlay);
      document.querySelectorAll('.illust-thumb, .illust-link, .illust-zoom').forEach(el => {{
        const src = el.dataset.full || el.getAttribute('href');
        if (!src) return;
        const alt = el.querySelector('img')
          ? el.querySelector('img').alt
          : el.textContent;
        const handler = (e) => {{ if (e) e.preventDefault(); openOverlay(src, alt); }};
        el.addEventListener('click', handler);
        el.addEventListener('keydown', e => {{
          if (e.key === 'Enter' || e.key === ' ') {{ e.preventDefault(); handler(); }}
        }});
      }});
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
    <a class="toc-pill" href="meta/ui/">Behind the Scenes</a>
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
