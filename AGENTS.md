# AGENTS.md (repo) — Book Arcade

This repository has two layers:

- `site/`: deployable static "book arcade" (Cloudflare Pages output)
- `books/`: source-of-truth projects for each book (drafts, bible, agents, tools)

## Golden Rules

- Treat `books/<slug>/INSTRUCTIONS.md` as the controlling prompt for that book. Do not edit it without explicit author intent.
- Do not hand-edit `site/books/<slug>/` content if it can be generated/copied from `books/<slug>/`.
- Prefer small, explicit, file-based workflows (no hidden state). Keep prompts, schemas, and style guides in-repo.

## Layout

Per-book source tree (authoring):

- `books/<slug>/manuscript/`: `chapter-NN.draft.md` (working) and `chapter-NN.html` (reader-ready)
- `books/<slug>/bible/`, `outline/`, `review/`: canon + planning + QA logs
- `books/<slug>/style/`: per-book reading CSS, fonts, and theme config
- `books/<slug>/schema/`: per-book structured data contracts (YAML/JSON)
- `books/<slug>/tools/`: utilities (lint, translation, asset generation)

Shared (cross-book) conventions live in:

- `shared/style/`: common font + CSS guidance (books may vendor/copy as needed)
- `shared/schema/`: common schema patterns and versioning notes

## Publishing To The Arcade

To publish a book into the deployable site, copy/sync the public artifacts into:

- `site/books/<slug>/`

Use:

- `python3 tools/publish_book.py --slug <slug>`

This is intentionally a "dumb sync" step: book source stays in `books/`, the arcade serves files from `site/`.

