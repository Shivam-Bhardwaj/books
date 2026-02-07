# AGENTS.md — The Sundering Agent Pack

This repo is designed to be iterated by multiple AI agents (Claude Code, Codex, Gemini, etc.). This file defines *how* those agents should behave and what they should output.

## Non-Negotiables

- `INSTRUCTIONS.md` is the operating manual. Follow it.
- Bible files in `bible/` are canon. If a chapter contradicts them, the chapter is wrong. Do not silently "fix canon"; flag it.
- Avoid full rewrites unless explicitly requested. Prefer targeted fixes.
- Every actionable issue must be emitted as a copy-ready line for `review/revision-queue.md` (format below).

## Revision Queue Format (Copy-Ready)

```text
- [ ] [CONTINUITY] Arc N, Ch NN: ... — Source: agent/<role>
- [ ] [SCIENCE] Arc N, Ch NN: ... — Source: agent/<role>
- [ ] [STRUCTURE] Arc N, Ch NN: ... — Source: agent/<role>
- [ ] [PROSE] Arc N, Ch NN: ... — Source: agent/<role>
```

Priority is: `CONTINUITY > SCIENCE > STRUCTURE > PROSE`.

## Recommended Per-Chapter Loop

1. Mechanical scan: `python3 tools/prose_lint.py manuscript/arc-N/chapter-NN.draft.md`
2. Structure: `agents/roles/structure-beat-reviewer.md`
3. Continuity: `agents/roles/continuity-reviewer.md`
4. Science: `agents/roles/science-reviewer.md`
5. Engagement: `agents/roles/beta-reader.md`
6. Line polish: `agents/roles/proofreader.md`

## Visuals (Midjourney + Runway)

- Default aspect ratio: **16:9**.
- No text, logos, or watermarks in generated visuals.
- Use `agents/visual/VISUAL_STYLE_BIBLE.md` as the consistent art direction.
- Prompts live in `agents/visual/chapter-visual-prompts.yaml` (generated) and can be regenerated with `python3 tools/generate_visual_prompts.py`.

## Hindi Localization

Hindi translation is a two-pass workflow:

1. `agents/roles/translator-hi.md` (faithful literary translation)
2. `agents/roles/hindi-naturalness-editor.md` (remove "robotic" feel; preserve voice differences)

Use `agents/translation/HINDI_STYLE.md` and `agents/translation/glossary-hi.yaml` for consistency.

## Multilingual Translation (Research-Grade)

- Baseline MT: `python3 tools/translate_chapter.py` (NLLB-only).
- Ensemble MT: `python3 tools/translate_chapter_ensemble.py` (multi-engine + scoring/QE).
- QC checks: `python3 tools/translation_qc.py`.
- Pipeline config: `agents/translation/translation-pipeline.yaml`.

## Roles

All role prompts live in `agents/roles/`:

- `beta-reader.md`
- `proofreader.md`
- `structure-beat-reviewer.md`
- `continuity-reviewer.md`
- `science-reviewer.md`
- `style-voice-reviewer.md`
- `language-consultant.md`
- `visual-midjourney.md`
- `visual-runway.md`
- `translator-hi.md`
- `hindi-naturalness-editor.md`
