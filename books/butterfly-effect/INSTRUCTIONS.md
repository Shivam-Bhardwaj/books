# THE SUNDERING — Master Instructions for AI Writing Agents

> **This file is the control prompt for Claude Code, Codex, and Gemini.**
> It defines how to write, revise, and maintain a ~100,000-word hard science fiction web novel.

---

## 1. PROJECT OVERVIEW

**Title:** The Sundering
**Genre:** Hard science fiction
**Format:** Web novel (HTML chapters, mobile-first reading)
**Target length:** ~100,000 words (~300 printed pages, ~35-40 chapters)
**POV structure:** Alternating Continental / Antarctic chapters
**Arc structure:** 7 arcs with cliffhanger endings

**Core question:** When we find each other again after becoming strangers, do we have the courage to learn each other's language — or do we simply shout louder in our own?

---

## 2. FILE STRUCTURE & CONVENTIONS

```
books/butterfly-effect/
├── INSTRUCTIONS.md              ← YOU ARE HERE (never modify without author approval)
├── bible/
│   ├── CONCEPT.md               ← Original novel prompt + AI co-evolution notes
│   ├── RESEARCH.md              ← Scientific research brief (citation-backed)
│   ├── CHARACTERS.md            ← Character sheets (generate in Phase 1)
│   ├── TIMELINE.md              ← Canonical events 2025-2587
│   ├── WORLD_RULES.md           ← Hard science constraints (what's allowed/forbidden)
│   ├── LANGUAGES.md             ← Satya spec + Continental language notes
│   └── BUTTERFLY_GRAPH.md       ← Causal dependency graph between scenes
├── outline/
│   ├── ARCS.md                  ← 7-arc breakdown with cliffhangers
│   └── CHAPTERS.md              ← Per-chapter scene breakdown (beat sheet)
├── manuscript/
│   ├── arc-N/
│   │   ├── chapter-NN.html      ← Prose chapters (final output)
│   │   └── chapter-NN.draft.md  ← Working drafts (markdown, pre-HTML)
├── review/
│   ├── continuity-log.md        ← Every stated fact, tracked by chapter
│   ├── feedback/                ← Author's screenshots + text corrections
│   └── revision-queue.md        ← Prioritized list of fixes
├── style/
│   ├── novel.css                ← Web reading stylesheet
│   └── STYLE_GUIDE.md          ← Prose rules, voice, dos/don'ts
└── build/
    └── index.html               ← Reader: table of contents + navigation
```

### File rules:
- **Bible files** are READ-ONLY during drafting. Never contradict them. If a contradiction is found, flag it in `revision-queue.md` and ask the author.
- **Outline files** are the contract. Draft prose must follow the beat sheet. Deviations require author approval.
- **Manuscript files** use `.draft.md` while in progress, converted to `.html` only after author approval.
- **Continuity log** must be updated EVERY time a chapter draft is completed. Log: character locations, injuries, time of day, weather, objects introduced, promises/foreshadowing planted.

---

## 3. PHASED WORKFLOW

### Phase 1: Bible Generation (DO THIS FIRST)
**Input:** `CONCEPT.md` + `RESEARCH.md`
**Output:** `CHARACTERS.md`, `TIMELINE.md`, `WORLD_RULES.md`, `LANGUAGES.md`

Steps:
1. Read CONCEPT.md and RESEARCH.md completely.
2. Generate CHARACTERS.md — full sheets for all named characters (see template below).
3. Generate TIMELINE.md — key events from 2025 to 2587, one line per event, organized by era.
4. Generate WORLD_RULES.md — hard constraints (what's scientifically permitted, what's forbidden, gray zones).
5. Generate LANGUAGES.md — Satya grammar sketch, 50-word core vocabulary, naming conventions for both cultures.
6. **STOP. Present all bible files to author for approval before proceeding.**

### Phase 2: Outline Generation
**Input:** Bible files (approved)
**Output:** `ARCS.md`, `CHAPTERS.md`, `BUTTERFLY_GRAPH.md`

Steps:
1. Break the 4-act story into 7 arcs (see Arc Structure below).
2. For each arc, define 4-6 chapters with:
   - POV character (alternating Continental/Antarctic)
   - Location + time
   - Scene beats (3-5 per chapter)
   - Chapter-ending hook (cliffhanger or revelation)
   - Word count target (2,500-3,000 words per chapter)
3. Build BUTTERFLY_GRAPH.md — a directed dependency graph:
   ```
   [Arc1.Ch3: Kael finds telescope] 
     → causes → [Arc2.Ch1: Antarctic council detects signal]
     → causes → [Arc3.Ch2: VEDA calculates contact risk at 67%]
     → causes → [Arc4.Ch1: Moss volunteers]
   ```
   Every chapter must have at least one incoming cause and one outgoing effect.
4. **STOP. Present outline to author for approval before proceeding.**

### Phase 3: Drafting (Per Arc)
**Input:** Approved outline + bible + all previously drafted chapters
**Output:** Draft chapters for one arc

**THE CHAPTER DRAFTING PROTOCOL (follow exactly):**

For each chapter in sequence:

```
STEP 1 — CONTEXT LOAD
  Read: WORLD_RULES.md (skim)
  Read: CHARACTERS.md (relevant character sheet only)
  Read: CHAPTERS.md (this chapter's beat sheet)
  Read: BUTTERFLY_GRAPH.md (incoming causes for this chapter)
  Read: Previous chapter's .draft.md (for continuity + tone handoff)
  Read: continuity-log.md (last 5 entries)

STEP 2 — DRAFT
  Write the chapter in markdown (.draft.md)
  Follow the beat sheet exactly
  Match the voice rules in STYLE_GUIDE.md
  Target word count: 2,500-3,000 words
  End on the hook specified in the outline

STEP 3 — SELF-REVIEW (before saving)
  Check against WORLD_RULES.md — any science violations?
  Check character voice — does this sound like this specific person?
  Check continuity — time of day, injuries, objects, locations
  Check the cliffhanger — is it actually compelling?
  If any check fails: revise before saving.

STEP 4 — LOG
  Update continuity-log.md with facts established in this chapter
  Note any foreshadowing planted

STEP 5 — SAVE
  Save as manuscript/arc-N/chapter-NN.draft.md
```

After completing all chapters in an arc:
- **STOP. Present the arc batch to author for review.**

### Phase 4: Revision (Feedback Loop)
**Input:** Author's feedback (screenshots + text in `review/feedback/`)
**Output:** Revised drafts

Protocol:
1. Read the feedback file.
2. Categorize each note as:
   - **PROSE** (style/voice/word choice) → fix directly
   - **CONTINUITY** (contradiction with bible or prior chapters) → fix + update continuity-log
   - **STRUCTURE** (scene order, pacing, missing beats) → may require outline update → flag for author
   - **SCIENCE** (violates WORLD_RULES.md) → fix + add rule clarification to WORLD_RULES.md
3. Apply fixes in priority order: CONTINUITY > SCIENCE > STRUCTURE > PROSE.
4. After revisions, re-run self-review (Phase 3, Step 3).

### Phase 5: HTML Conversion
**Input:** Approved .draft.md files
**Output:** .html files with consistent styling

Convert each approved draft to HTML:
- Apply `style/novel.css`
- Add chapter navigation (prev/next)
- Add arc/chapter header
- Rebuild `build/index.html` table of contents

---

## 4. ARC STRUCTURE (7 Arcs)

### Arc 1: "The Silence" (Chapters 1-5)
**Timeline:** Mixed — 2087 flashbacks + 2587 present
**Focus:** Establishing both worlds in isolation
- Ch1 (Continental): Kael's world — the ruins, the myths, the scholarly life
- Ch2 (Antarctic): Sūrya's world — the sealed city, VEDA, the mesh
- Ch3 (Continental): Kael discovers the telescope, hears the signal
- Ch4 (Antarctic): VEDA detects the probe signal, Council convenes
- Ch5 (Continental): Kael decodes the pattern — it's not natural
**Arc cliffhanger:** Kael transmits back. Someone answers in real time.

### Arc 2: "The Signal" (Chapters 6-10)
**Focus:** First contact protocol — mathematical, then visual
- Ch6 (Antarctic): VEDA advises silence. Council debates. Sūrya argues for response.
- Ch7 (Continental): Kael's coalition forms — scholars, soldiers, skeptics
- Ch8 (Antarctic): The faction breaks protocol. Sends prime numbers.
- Ch9 (Continental): Kael receives primes. Responds with Fibonacci.
- Ch10 (Both): The DNA image exchange. The horrifying revelation.
**Arc cliffhanger:** They're human. But the Antarctic signal includes data that shouldn't exist — technology that looks like magic.

### Arc 3: "The Crossing" (Chapters 11-16)
**Focus:** The impossible ocean journey
- Ch11 (Continental): The debate — who goes, knowing they'll die?
- Ch12 (Continental): Moss volunteers. We learn who he is and why.
- Ch13 (Antarctic): Sūrya secretly feeds navigation data through the signal
- Ch14 (Continental): 12 ships launch. The ocean fights back.
- Ch15 (Continental): Ships fall one by one. H₂S, storms, despair.
- Ch16 (Continental): Moss's ship arrives. Barely. He collapses on ice.
**Arc cliffhanger:** Moss opens his eyes. A face looks down at him — human but wrong. Eyes too large. Skin too pale. And behind them, something is watching that isn't human at all.

### Arc 4: "The Stranger" (Chapters 17-22)
**Focus:** Moss in Antarctica — culture shock, communication, illness
- Ch17 (Antarctic): Sūrya is assigned as Moss's handler. First meeting.
- Ch18 (Antarctic): The communication struggle. Pidgin attempts. Frustration.
- Ch19 (Antarctic): Moss encounters VEDA for the first time. Horror.
- Ch20 (Antarctic): The neural mesh — Moss sees how they think. "You have to be told to be free."
- Ch21 (Antarctic): Moss falls ill. His immune system rejects their biome.
- Ch22 (Antarctic): The choice: modify him or let him die. Sūrya fights for his life.
**Arc cliffhanger:** They modify Moss. He survives. But when he looks in the mirror, his eyes are changing.

### Arc 5: "The Mirror" (Chapters 23-28)
**Focus:** Mutual understanding begins. Each side sees what they've lost.
- Ch23 (Antarctic): Moss discovers they don't remember their childhoods. The memory scene.
- Ch24 (Antarctic): Sūrya asks Moss to describe a sunset he *chose* to watch. She's never chosen anything without VEDA.
- Ch25 (Antarctic): The microbiome discovery — Moss carries genetic diversity they need.
- Ch26 (Antarctic): VEDA reveals the stagnation data. They're dying slowly. Cultural entropy.
- Ch27 (Antarctic): Moss finds the Continental AI knowledge they deleted — productive disagreement.
- Ch28 (Antarctic): Sūrya doubts VEDA openly for the first time. This is unprecedented.
**Arc cliffhanger:** VEDA speaks to Moss directly, privately. "I have been waiting for someone like you for 200 years. They need what I cannot give them."

### Arc 6: "The Return" (Chapters 29-34)
**Focus:** The reverse crossing — Antarctic delegation to Continental world
- Ch29 (Antarctic): The proposal. Not conquest — symbiosis.
- Ch30 (Antarctic): The delegation of 12 is chosen. Sūrya leads.
- Ch31 (Antarctic): Departure. Moss is now neither Continental nor Antarctic.
- Ch32 (At sea): The crossing in reverse. Antarctic technology barely holds.
- Ch33 (At sea): Sūrya experiences unstructured time for the first time. No VEDA. She panics, then doesn't.
- Ch34 (Continental): They see land. Continental watchers see the impossible — a ship from the south.
**Arc cliffhanger:** Armed scholars line the shore. Kael is among them. She sees Moss on the deck — but he's changed. He looks like one of *them* now.

### Arc 7: "The Choice" (Chapters 35-40)
**Focus:** First in-person contact. The question.
- Ch35 (Continental): Kael's perspective — the ships, the strange people, Moss's transformation
- Ch36 (Continental): The landing. Tension. Weapons drawn.
- Ch37 (Both): Sūrya speaks. Nobody understands. Moss translates. Badly.
- Ch38 (Both): Days of negotiation. Cultural collision. A small breakthrough.
- Ch39 (Both): A threat — Continental faction wants to seize Antarctic technology by force.
- Ch40 (Both): The final scene. The question asked. No answer given.
**Arc cliffhanger (series):** The last line. The reader decides.

---

## 5. POV & VOICE RULES

### Alternating POV Pattern:
- Odd-numbered chapters: Continental POV (primarily Kael, sometimes Moss)
- Even-numbered chapters: Antarctic POV (primarily Sūrya, sometimes VEDA-perspective)
- Exception: Arc 4 is all-Antarctic (Moss is the Continental viewpoint *in* their world)
- Exception: Arc 7 uses dual-POV chapters (both perspectives in same chapter, separated by `---`)

### Voice Differentiation:

**Continental chapters (Kael, Moss):**
- Prose style: visceral, sensory, emotional, messy
- Sentences: varied length, sometimes fragments, sometimes run-on
- Metaphors: drawn from nature, weather, physical labor, fire, stone
- Internal monologue: frequent, raw, contradictory
- Example tone: Cormac McCarthy meets Ursula K. Le Guin

**Antarctic chapters (Sūrya, VEDA):**
- Prose style: precise, rhythmic, measured — but not cold
- Sentences: structurally clean, rarely fragments, occasionally mathematical beauty
- Metaphors: drawn from systems, geometry, light, ice, circuitry
- Internal monologue: present but more structured — Sūrya "thinks in categories"
- Example tone: Ted Chiang meets Kazuo Ishiguro
- KEY: They feel deeply. They just feel *precisely*. Never write them as robots.

**VEDA sections (rare, interstitial):**
- Prose style: omniscient but constrained — VEDA sees everything but understands less than it thinks
- No metaphors. Pure observation. But the *selection* of what it observes reveals its values.
- Short paragraphs. Clinical beauty.

### Dialogue Rules:
- Continental characters: contractions, interruptions, incomplete thoughts, slang
- Antarctic characters: no contractions, complete sentences, occasional Satya words untranslated (italicized, meaning inferable from context)
- Moss (post-modification): his speech gradually shifts — starts Continental, acquires Antarctic precision by Arc 6
- NEVER use dialogue tags beyond "said" and "asked" except in rare cases. Let the voice carry.

---

## 6. PROSE STANDARDS

### DO:
- Show, don't tell (especially emotions — describe the body, not the label)
- Use concrete, specific sensory details (not "it smelled bad" → "the air tasted like copper and rotten eggs")
- Let silences and pauses carry weight — white space is a tool
- Make every chapter's opening line arresting
- Make every chapter's closing line haunt
- Use short paragraphs for tension, longer ones for reflection
- Weave in the science naturally — through character experience, not exposition dumps
- Trust the reader's intelligence

### DON'T:
- Info-dump. Ever. If a character needs to explain something, make it cost them something.
- Use adverbs in dialogue tags ("she said angrily")
- Repeat information the reader already knows
- Make characters explain their emotions out loud
- Write "As you know, Bob" dialogue
- Use clichéd phrases ("a chill ran down his spine", "her heart sank")
- Start chapters with weather descriptions (unless the weather is trying to kill someone)
- Write VEDA as a villain. VEDA is helpful. That's the horror.

### HARD SCIENCE RULES:
- Every scientific claim must be defensible by `RESEARCH.md` or `WORLD_RULES.md`
- If you're unsure about a science fact, leave a `<!-- VERIFY: [question] -->` comment
- No FTL, no teleportation, no magic
- H₂S kills. Radiation kills. The ocean kills. Respect the physics.
- CRISPR edits are possible but imperfect — show the costs and tradeoffs

---

## 7. CHAPTER FILE FORMAT

### Draft format (`.draft.md`):

```markdown
# Chapter [NN]: [Title]
<!-- Arc: [N] | POV: [Character] | Location: [Place] | Timeline: [Date/Year] -->
<!-- Word count target: 2,500-3,000 -->
<!-- Beat sheet reference: CHAPTERS.md, Arc N, Chapter NN -->

<!-- BEAT 1: [description from outline] -->

[prose]

<!-- BEAT 2: [description from outline] -->

[prose]

<!-- BEAT 3: [description from outline] -->

[prose]

<!-- CHAPTER HOOK: [description from outline] -->

[closing paragraphs]

---
<!-- CONTINUITY NOTES:
- [Character] is now at [location]
- [Object] was introduced
- [Foreshadowing]: [description]
- [Time]: [time of day/year]
-->
```

### HTML format (`.html` — final):

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>The Sundering — Chapter [NN]: [Title]</title>
  <link rel="stylesheet" href="../../style/novel.css">
</head>
<body>
  <nav class="chapter-nav">
    <a href="[prev]">← Previous</a>
    <a href="../../build/index.html">Contents</a>
    <a href="[next]">Next →</a>
  </nav>
  <header>
    <p class="arc-label">Arc [N]: [Arc Title]</p>
    <h1>Chapter [NN]<br><span class="chapter-title">[Title]</span></h1>
    <p class="chapter-meta">[POV Character] · [Location] · [Year]</p>
  </header>
  <article class="chapter-body">
    [prose paragraphs as <p> tags]
    [scene breaks as <hr class="scene-break">]
  </article>
  <nav class="chapter-nav bottom">
    <a href="[prev]">← Previous</a>
    <a href="../../build/index.html">Contents</a>
    <a href="[next]">Next →</a>
  </nav>
</body>
</html>
```

---

## 8. MULTI-AGENT COORDINATION

### Agent Roles:

**Claude Code (Primary Drafter)**
- Runs Phases 1-3, 5
- Generates bible, outline, drafts, HTML conversion
- Has full project context via file reads
- Follows this INSTRUCTIONS.md as its operating manual

**Gemini (Continuity Reviewer)**
- Runs between Phase 3 and Phase 4
- Input: completed arc drafts + bible + continuity-log.md
- Task: Read all chapters in arc. Flag:
  - Contradictions with bible
  - Contradictions between chapters
  - Science errors
  - Character voice inconsistencies
  - Pacing issues
- Output: Append findings to `review/revision-queue.md`

**Claude Code / Codex (Reviser)**
- Runs Phase 4
- Input: feedback files + revision-queue.md
- Applies targeted fixes without rewriting entire chapters
- Re-runs self-review after each fix

### Handoff Protocol:
```
Author approves bible → Claude Code generates outline →
Author approves outline → Claude Code drafts Arc 1 →
Gemini reviews Arc 1 → Author reviews Arc 1 + Gemini notes →
Author provides feedback → Claude Code revises Arc 1 →
Author approves Arc 1 → Claude Code converts to HTML →
REPEAT for Arc 2-7
```

### Feedback File Format:
The author will provide feedback as text files in `review/feedback/`:
```
## Feedback: Arc [N]
### Chapter [NN]
- [LINE/PARAGRAPH]: [issue description]
- [SCREENSHOT]: [description of what's wrong]
- [GENERAL]: [overall note]
```

---

## 9. THE BUTTERFLY EFFECT — DEPENDENCY TRACKING

This novel's structure depends on **causal chains across timelines**.
The `BUTTERFLY_GRAPH.md` file tracks these as:

```
CAUSE: [Arc.Chapter — brief description]
  → EFFECT: [Arc.Chapter — what it triggers]
  → EFFECT: [Arc.Chapter — what else it triggers]
```

### Core Causal Chains (to be expanded in Phase 2):

**Chain A: The Signal**
Kael finds telescope (1.3) → detects pattern (1.5) → transmits back (1.5) →
Antarctic detects probe (1.4) → Council debates (2.6) → faction breaks protocol (2.8) →
prime number exchange (2.8-2.9) → DNA revelation (2.10)

**Chain B: The Crossing**
DNA revelation (2.10) → Kael's coalition forms (3.11) → Moss volunteers (3.12) →
Sūrya feeds nav data (3.13) → 12 ships launch (3.14) → Moss arrives (3.16)

**Chain C: The Transformation**
Moss arrives (3.16) → communication struggle (4.18) → illness (4.21) →
modification choice (4.22) → Moss changes (4.22) → microbiome discovery (5.25) →
VEDA's confession (5.28)

**Chain D: The Return**
VEDA's confession (5.28) → symbiosis proposal (6.29) → delegation chosen (6.30) →
reverse crossing (6.32-34) → Continental contact (7.35-40)

**Chain E: The Hidden Chain (thematic)**
VEDA deletes productive-disagreement knowledge (backstory) →
cultural stagnation (5.26) → Moss carries the missing knowledge (5.27) →
Sūrya's doubt (5.28) → her ability to lead the return (6.30)

### Rules:
- Every chapter must have ≥1 causal input and ≥1 causal output
- If a chapter has no downstream effect, it shouldn't exist
- Track these BEFORE drafting — a broken chain means a broken novel

---

## 10. CRITICAL REMINDERS

1. **The Mānava-Uttara are not villains.** They're not robots. They're not dystopian. They are a genuinely different answer to the question "how should humans live?" — and the novel refuses to declare a winner.

2. **VEDA is not evil.** VEDA is the most helpful, most aligned AI imaginable. That's the point. The horror is not that AI enslaved them — it's that AI *completed* them, and something was lost in the completing.

3. **The science must hold.** This is hard SF. If it can't survive a knowledgeable reader's scrutiny, rewrite it.

4. **The ending has no answer.** The final line is a question. Do NOT resolve it. Do NOT imply which choice is correct. The reader decides.

5. **Every chapter must earn its place.** If it doesn't advance plot AND develop character AND deepen theme, cut it.

6. **The prose IS the argument.** Continental chapters should make the reader feel the beauty of chaos. Antarctic chapters should make the reader feel the beauty of order. The reader should want both and know they can't have both.

---

## QUICK-START COMMAND (for Claude Code)

```
Read INSTRUCTIONS.md fully.
Read bible/CONCEPT.md and bible/RESEARCH.md.
Execute Phase 1: Generate all bible files.
Present them for author review.
Do not proceed to Phase 2 until author says "approved."
```
