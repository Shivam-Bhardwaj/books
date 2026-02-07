# Chapter Sigils (SVG)

This folder contains one SVG per chapter, used by the web reader as lightweight thematic icons.

Source of truth for themes/prompts: `style/chapter-svg-themes.yaml`

Generation:
- Placeholder sigils can be generated with `python3 tools/generate_sigils_placeholder.py`.
- A separate art-focused agent can later replace these SVGs with hand-designed monoline sigils (same filenames/ids).

Constraints (summary):
- No text in SVG.
- `viewBox="0 0 256 256"`.
- `stroke="currentColor"`, `fill="none"`.
- Legible at 24px.

