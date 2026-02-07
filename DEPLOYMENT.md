# Deployment

This repo serves static files from `site/` (Cloudflare Pages output).

## Local Preview

Option A (simple static server):

```bash
python3 -m http.server 8788 --directory site
```

Option B (Cloudflare Pages emulation):

```bash
npm run dev
```

## Sync Books Into `site/`

Keep the arcade output in sync with the book sources:

```bash
npm run sync
```

This runs each book's `build/convert.py` (if present) and publishes into `site/books/<slug>/`.

## Deploy To Cloudflare Pages

Preview (non-production branch):

```bash
npm run deploy:preview
```

Production (adjust `--branch` to match your Pages project's production branch):

```bash
npm run deploy:prod
```

## Feedback Loop (Screenshots + JSON)

Run an audit that renders key pages (desktop + mobile) and writes screenshots plus reports:

```bash
npm run audit
```

Outputs:
- `artifacts/site-audit/site-audit.md`
- `artifacts/site-audit/site-audit.json`

