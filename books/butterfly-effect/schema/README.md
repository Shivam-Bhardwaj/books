# Sundering Schema (SunderingIR v1)

This project is written *with* AI agents. Agents perform best when they have a compact, structured representation of:

- Canon entities (characters/places/concepts)
- Chapter intent (beats + hook)
- Continuity state (facts that must remain consistent)
- Translation constraints (what must not drift across languages)

This folder is an **intermediate representation** (IR) that sits between raw prose (`manuscript/`) and agent workflows (`agents/`).

## Files

- `schema/entities.yaml`
  - Registry of story entities and "do not translate" tokens.
  - Intended for translation, visual prompting, and consistency checks.

- `schema/chapter-cards.yaml`
  - One record per chapter: POV, setting, beats, hook, and thematic motif.
  - Generated from `outline/CHAPTERS.md` + `style/chapter-svg-themes.yaml`.

## Generation

Rebuild chapter cards after updating the outline or chapter theme list:

```bash
python3 tools/build_chapter_cards.py
```

## Why This Helps Translation

Pure machine translation often fails on novels because it lacks:

- POV register consistency (Continental vs Antarctic voice split)
- Character continuity (who is speaking, what the world feels like)
- Term stability (VEDA, mesh, Satya, SĀDHU, etc.)
- The chapter's *intent* (the hook and the emotional turn)

The chapter cards provide that context so a post-edit pass (human or LLM) can make translations feel organic.

