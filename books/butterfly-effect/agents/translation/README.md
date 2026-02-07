# Translation Pipeline

This repo supports **local GPU translation** for web-novel chapters, with a focus on:
- preserving voice (Continental vs Antarctic)
- protecting canon tokens (names, acronyms, Satya terms)
- producing *multiple candidates* and selecting a best result algorithmically

## Quick Start

Baseline (NLLB only):

```bash
python3 tools/translate_chapter.py --chapter manuscript/arc-1/chapter-01.draft.md --lang hi es ru ar zh-hans ko
```

Ensemble (multi-engine + scoring/QE):

```bash
python3 tools/translate_chapter_ensemble.py --chapter manuscript/arc-1/chapter-01.draft.md --lang hi es ru ar zh-hans ko
```

Outputs to:
- `translations/<lang>/arc-N/chapter-NN.md`
- `translations/<lang>/arc-N/chapter-NN.report.json`

## Config

Edit:
- `agents/translation/translation-pipeline.yaml`

Key switches:
- `engines.*.enabled`: turn engines on/off
- `selection.mode`: `chapter` (default) vs `paragraph`
- `qe.cometkiwi.enabled`: reference-free QE (often requires HF token + license acceptance)
- `qe.embed_fallback`: deterministic cross-lingual similarity scorer (always available)

## Quality Checks

After generating a translation:

```bash
python3 tools/translation_qc.py --src manuscript/arc-1/chapter-01.draft.md --mt translations/hi/arc-1/chapter-01.md
```

This catches hard failures like:
- protected token dropped/translated
- paragraph/scene-break drift
- leftover placeholders

## Post-Edit (Where "Organic" Happens)

Machine translation is a baseline. For a non-robotic, emotionally equivalent rendering:
- use the chapter's `schema/chapter-cards.yaml` voice hints
- run a language-specific post-edit agent (e.g. Hindi has `agents/roles/hindi-naturalness-editor.md`)
- keep token/glossary constraints; edit around them

