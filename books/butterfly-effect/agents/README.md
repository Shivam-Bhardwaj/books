# The Sundering: Agent Pack

This folder contains model-agnostic prompt files for running specialized "agents" (reviewers, editors, translators, visual prompters) against this repo's chapters and bibles.

## How To Use

1. Pick a role prompt from `agents/roles/`.
2. Provide the agent with:
- The target chapter draft `manuscript/arc-N/chapter-NN.draft.md`
- `style/STYLE_GUIDE.md`
- The relevant bible(s): usually `bible/WORLD_RULES.md`, `bible/CHARACTERS.md`, `bible/TIMELINE.md`, `bible/LANGUAGES.md`
- The relevant outline slice from `outline/CHAPTERS.md`
- Recent continuity entries from `review/continuity-log.md`
3. Paste the agent output into:
- `review/revision-queue.md` for prioritized fixes
- `review/continuity-log.md` for new facts (after the chapter is finalized)

If the model has file system access (Claude Code, Codex), it should read the files directly. If it does not, paste the required files or excerpts into the chat.

## Output Conventions

For anything that should become an actionable task, the agent should emit copy-ready lines in this exact format (to append to `review/revision-queue.md`):

```text
- [ ] [CONTINUITY] Arc N, Ch NN: ... — Source: agent/<role>
- [ ] [SCIENCE] Arc N, Ch NN: ... — Source: agent/<role>
- [ ] [STRUCTURE] Arc N, Ch NN: ... — Source: agent/<role>
- [ ] [PROSE] Arc N, Ch NN: ... — Source: agent/<role>
```

## Recommended Review Loop (Per Chapter)

1. Run `tools/prose_lint.py` for mechanical issues.
2. Run `continuity-reviewer.md` (facts and contradictions).
3. Run `science-reviewer.md` (WORLD_RULES compliance).
4. Run `beta-reader.md` (engagement, clarity, hooks).
5. Run `proofreader.md` last (line-level polish after structure is stable).
6. Generate visuals with `visual-midjourney.md` and `visual-runway.md`.
7. Translate with `translator-hi.md`, then refine with `hindi-naturalness-editor.md`.

If you are running multiple reviewers, finish with `editor-in-chief.md` to dedupe, prioritize, and turn reports into a minimal fix plan.
