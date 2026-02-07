# books.too.foo

Static, extremely lightweight "book arcade" entry point.

## Structure

- `site/`: deployable static arcade (Cloudflare Pages output)
- `books/`: source projects for each book (drafts, bible, agents, tools)
- `shared/`: cross-book conventions (fonts, schema patterns, style guidance)

Deploy only `site/`. Author in `books/`.

## Books

- Source-of-truth: `books/<slug>/`
- Published output: `site/books/<slug>/`

Publish (sync) a book into the arcade:

```bash
python3 tools/publish_book.py --slug butterfly-effect
```

Sync all books (and run `build/convert.py` where present):

```bash
python3 tools/sync_site.py
```

## Local dev

Option A (no Node):

```bash
python3 -m http.server 8788 --directory site
```

Option B (Wrangler / Cloudflare Pages emulation):

```bash
npm run dev
```

## Deploy (Cloudflare Pages)

Configure the Pages project to use:

- Build command: none
- Output directory: `site`

Or deploy with Wrangler:

```bash
wrangler pages deploy site --project-name books-too-foo
```

See `DEPLOYMENT.md` for preview vs production deploy commands and the audit loop.

## Notes

- Prefer not to edit `site/books/<slug>/` by hand; treat it as published output from `books/<slug>/`.
- If you use Obsidian, the vault lives at the repo root; book notes should be inside `books/<slug>/`.
