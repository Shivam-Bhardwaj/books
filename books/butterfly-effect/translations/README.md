# Translations

This folder is for machine-generated translations + post-edited versions.

## Local GPU MT (Baseline)

This repo includes a local translation script powered by **NLLB** (text MT).

Translate one chapter:

```bash
python3 tools/translate_chapter.py --chapter manuscript/arc-1/chapter-01.draft.md --lang hi
```

Outputs to: `translations/hi/arc-1/chapter-01.md`

Translate multiple languages:

```bash
python3 tools/translate_chapter.py --chapter manuscript/arc-1/chapter-01.draft.md --lang hi es ru ar zh-hans ko
```

## Research-Grade Pipeline (Ensemble + QE/Scoring)

For better robustness and less "single-model brittleness", use the ensemble pipeline:

```bash
python3 tools/translate_chapter_ensemble.py --chapter manuscript/arc-1/chapter-01.draft.md --lang hi es ru ar zh-hans ko
```

This:
- Generates candidates from multiple local MT engines (see `agents/translation/translation-pipeline.yaml`)
- Selects a best engine per chapter by default (keeps voice consistent)
- Writes a small `.report.json` alongside the translation with scores + selection

If you want COMETKiwi (reference-free QE), you may need a venv + HF license acceptance/token.

## Post-Edit (Recommended)

Machine translation will not preserve:

- Continental vs Antarctic voice split
- Pidgin "brokenness" without becoming unreadable
- Metaphor pools (glass/sea vs geometry/light)

Run a post-edit pass using the agent prompts:

- `agents/roles/hindi-naturalness-editor.md`
- (Add equivalents for other languages as you scale)
