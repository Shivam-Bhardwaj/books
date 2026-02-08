# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

books.too.foo is a platform for writing and publishing books fast. The author provides imagination and creative direction. AI thinks and executes — structure, prose, conversion, publishing, and all code. Butterfly Effect is the pilot book; the system is built to scale to many.

## Architecture

Two layers:

- **`books/<slug>/`** — Source of truth (drafts, bible, style, build tools). Author works here.
- **`site/`** — Deployable static output. Generated, never hand-edited.

Pipeline: `books/<slug>/build/convert.py` converts `.draft.md` → `.html` chapters + TOC → `tools/publish_book.py` syncs into `site/books/<slug>/` → Cloudflare Pages serves `site/`.

## Commands

```bash
# Dev server
npm run dev                    # wrangler + live-reload on :8788
python3 -m http.server 8788 --directory site   # lightweight alternative

# Build & publish
npm run sync                   # convert + publish all books → site/
python3 tools/publish_book.py --slug butterfly-effect  # single book

# Test
npm run test:e2e               # all Playwright tests (auto-starts server)
npx playwright test tests/e2e/book.spec.mjs            # single file

# Audit (screenshots + JSON report across viewports/themes)
npm run audit                  # → artifacts/site-audit/

# Deploy
npm run deploy:preview
npm run deploy:prod
```

## Testing

Playwright e2e in `tests/e2e/`. Two projects: `chromium-light` and `chromium-dark`. Auto-starts a Python static server on :8788 (override: `E2E_BASE_URL`).

Tests enforce the design rules below — font loading, color scheme, paragraph styling, navigation integrity.

## Design Rules

These are the visual and UX standards extracted from the codebase. Follow them for any UI work.

### Color & Theme
- **Paper-first.** The reading experience forces `color-scheme: light` — warm paper tones (`#f5efe4`, `#fbf7f0`) even when the OS is in dark mode. This is intentional; tests enforce it.
- Arcade home uses a similar warm palette (`--paper: #fbf7ef`).
- Accent colors: ember (`#e4572e`) and sea glass (`#2a9d8f`) on the arcade; cool teal (`#155e6b`) and warm amber (`#a85a2a`) in the reader.
- Subtle radial gradient blushes on backgrounds — never flat, never loud.

### Typography
- **Reader body:** Literata (variable weight serif, self-hosted woff2). Fallbacks: Iowan Old Style → Charter → Palatino → system serif.
- **UI elements:** Space Grotesk (variable weight sans, self-hosted woff2). Used for nav, labels, meta, arc headings.
- **Arcade home:** System UI sans-serif stack (`--font-ui`), display serif stack for headings (`--font-display`).
- Both fonts must load — tests verify `document.fonts.check()` for Literata and Space Grotesk.
- Font rendering: `font-optical-sizing: auto`, `font-kerning: normal`, `font-variant-ligatures: common-ligatures contextual`, antialiased.

### Reading Layout
- Max measure: `72ch` default, `78ch` at 900px+, `82ch` at 1200px+.
- `text-align: justify` with `hyphens: auto`. Tests enforce this.
- `text-wrap: pretty` for better line breaking.
- Paragraph indent (`1.5em`) instead of spacing between paragraphs. First paragraph has no indent.
- First chapter letter gets a drop cap on desktop (disabled on mobile <600px).
- Line height: `1.68` for body prose.

### Components
- **Progress bar:** Fixed 2px accent bar at top of chapter pages, driven by scroll position.
- **Scene breaks:** `· · ·` centered, via CSS `::before` on `hr.scene-break`.
- **Chapter sigils:** Per-chapter SVG illustrations (56px desktop, 50px tablet, 28px mobile), mapped in `style/chapter-svg-themes.yaml`.
- **Sticky nav:** Chapter nav sticks to top on desktop, static on mobile (<600px).
- **TOC pills:** Rounded pill buttons for navigation (`border-radius: 999px`).
- **Cards (arcade):** 12-column grid, glassmorphic cards with hover lift animation, `border-radius: 22px`, staggered entry animation.

### Responsiveness
- Mobile breakpoint: 600px (reader), 860px (arcade cards).
- Content padding: `1.25rem` default, `1rem` on mobile.
- `prefers-reduced-motion`: animations and transitions disabled.
- Print styles strip nav and flatten to black-on-white.

### Accessibility
- Semantic HTML: `<article>`, `<nav>`, `<header>`, `aria-label` on nav regions.
- Focus-visible outlines on interactive elements.
- `loading="lazy" decoding="async"` on all images.
- Keyboard-navigable chapter links.

## Prose Style Rules (All Books)

These rules apply to all prose written or edited by any agent. They are non-negotiable.

- **No em dashes (`—`).** Never use long dashes. Use short sentences, commas, periods, or semicolons instead. Em dashes are an AI writing tell. Rewrite any sentence that relies on them.
- **No archaic or literary-sounding phrasing.** Write like a modern person talks. No "upon which", "henceforth", "thus", "wherein", "amidst", "betwixt", "lest". Use "on", "from now on", "so", "where", "in the middle of", "between", "or else".
- **No vocabulary that sends readers to a dictionary.** If a word wouldn't appear in a casual conversation, replace it with a simpler one. The story should be accessible to anyone.
- **Short, clear sentences preferred.** Long compound sentences are fine occasionally, but the default should be punchy and direct.
- **No filler hedging.** Cut "seemed to", "appeared to", "began to", "started to" unless the ambiguity is genuinely meaningful.
- **Show, don't decorate.** No purple prose. One strong verb beats two weak ones with an adverb.

## Key Conventions

- `books/<slug>/INSTRUCTIONS.md` is the controlling prompt for that book — do not modify without author intent.
- Bible files (`books/<slug>/bible/`) are read-only during drafting.
- Drafts are `.draft.md`; final output is `.html` via the build pipeline.
- `novel.css` = per-book reader stylesheet. `styles.css` = arcade home stylesheet. Keep them separate.
- `book.yaml` at book root defines metadata (title, subtitle, navigation links).
- `_redirects` in `site/` handles vanity routes (e.g., `/butterfly-effect/` → book TOC).
