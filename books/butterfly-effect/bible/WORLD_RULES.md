# WORLD_RULES.md — Hard Science Constraints

> **Butterfly Effect** · Bible Document
> Status: DRAFT — awaiting author approval
> Last updated: 2026-02-06

---

## Purpose

This file defines what is **scientifically permitted**, **forbidden**, and **gray-zone** in the novel. Every scene must be defensible against this document. If a draft contradicts a rule here, the draft is wrong.

---

## 1. THE SUNDERING — Why the World Broke

### 1.1 The Carrington Cascade (2087–2089)

A cluster of X45+ solar flares over 18 months. Not one event — a sustained bombardment.

**What it did:**
- Destroyed >95% of satellite infrastructure via radiation damage and debris cascade
- Induced permanent Kessler syndrome in LEO through GEO
- Expanded Van Allen belt hazard zones, making orbital insertion lethal to unshielded electronics (failure threshold: ~10–20 krad TID for non-radhard systems)
- Created chronic D-layer ionization spikes, making HF radio unreliable (not permanently dead, but unusable for sustained coordination)
- Fried ground-level power grids across the sunlit hemisphere during peak events

**RULE:** No functioning satellites exist in 2587. No orbital infrastructure. Launch is theoretically possible but pointless — anything above 200 km altitude is cooked by radiation and shredded by debris. This is permanent on civilizational timescales without a coordinated global cleanup effort, which requires the global coordination that was destroyed.

### 1.2 Ocean Chemistry Collapse — The Canfield Regression

**Mechanism:** Climate feedback loops → ocean warming → deoxygenation → stratification → sulfate-reducing bacteria dominate → hydrogen sulfide (H₂S) production at depth → periodic venting to surface.

**What it looks like in 2587:**
- **Not a globally uniform dead ocean.** Regional euxinia concentrated in mid-latitude corridors, upwelling zones, and continental shelves
- "Kill belts" where H₂S vents to surface during upwelling events, calm weather, or storm mixing
- Purple-green bacterial mats visible on surface water in affected zones
- Coastal dead zones extend 100–300 km offshore in worst regions

**Hard numbers:**
- H₂S at **100 ppm** in breathing air = immediately life-threatening (IDLH)
- H₂S at **300+ ppm** = unconsciousness in minutes, death in minutes
- Surface venting events are **intermittent**, not constant — but unpredictable without satellite weather data
- Steel corrosion rate in sulfidic water: millimeters per year (ship hulls fail in weeks to months of continuous exposure)
- Microbiologically influenced corrosion (MIC) attacks metals, cable armor, and fasteners

**RULE:** The ocean is not a wall — it's a roulette wheel. Some days, some corridors are survivable. But without satellites, weather forecasting, or reliable comms, you cannot predict which days or which corridors. Every crossing is a gamble with terrible odds.

### 1.3 Storm Corridors

**Mechanism:** Ocean warming + jet stream destabilization → semi-permanent mega-storm lanes across major ocean basins.

**What it looks like:**
- Not one eternal hurricane. A statistical inevitability: at any given time, some segment of any trans-oceanic route is in severe sea state
- Sustained significant wave heights of 15–25 meters in storm corridors
- Safe weather windows exist but collapse faster than a vessel can exploit them (weeks-long crossings require weeks-long windows — those don't occur)
- True hypercanes (Emanuel-class, requiring ~50°C SST) are **rare edge cases**, not the norm. They occur perhaps once per decade in the worst basins. The daily reality is "merely" Category 4–5 equivalents that wander and stall

**RULE:** No single storm is the barrier. The barrier is the *absence of predictability*. Ships can survive any one storm. They cannot survive a crossing where storms appear without warning, navigation is dead-reckoning, and rescue is impossible.

### 1.4 Communications Collapse

**What works in 2587:**
- **Line-of-sight radio** (VHF/UHF): functional up to ~50 km over flat terrain/water. Used locally.
- **VLF/ELF**: technically functional via Earth-ionosphere waveguide, but requires enormous antenna infrastructure (kilometers of wire), delivers only a few characters per minute, and is one-directional for practical purposes. The Antarctikans might maintain one. The Continentals lost the knowledge.
- **Physical messenger**: works on land. Doesn't cross oceans.
- **Optical signals**: fires, mirrors, semaphore. Short range.

**What doesn't work:**
- HF skywave: intermittently absorbed by D-layer ionization events. Unpredictable. You might get through once in twenty attempts. You cannot sustain a conversation, let alone coordinate navigation.
- Satellites: see 1.1. Gone.
- Undersea cables: corroded by sulfidic water within years. Cable-laying ships can't survive the crossing. Last cables failed by ~2120.

**RULE:** Trans-oceanic communication is effectively impossible. Not absolutely impossible — a VLF signal might theoretically reach, a lucky HF bounce might land — but sustained, reliable, two-way communication across oceans does not exist. The signal Kael detects in 2587 is extraordinary precisely because it shouldn't be possible.

### 1.5 The Signal — How It Works (Exception to Rule 1.4)

Kael discovers a **functioning radio telescope** in the ruins of the Arecibo-successor facility (rebuilt before the Cascade, partially survived due to passive construction). She detects a pattern — not natural.

The Antarctic side: VEDA maintains a **VLF transmitter array** (kilometers of antenna wire in the ice) for environmental monitoring. It has been sending patterned signals for centuries as a passive "anyone out there?" probe. The signal is extremely low bandwidth — a few bits per second.

**RULE:** The initial contact is agonizingly slow. Days to exchange a single meaningful message. The "conversation" in Arcs 1–2 happens over weeks and months, not minutes. This constraint is non-negotiable — it drives the plot's pacing and the communication protocol scenes.

---

## 2. ANTARCTICA — The Sealed World

### 2.1 Geography and Infrastructure

**Location:** West Antarctica, primarily over Marie Byrd Land geothermal province and extending toward the Thwaites/Pine Island region. Multiple interconnected sealed habitats, not one megacity.

**Population:** ~50,000 (stable, maintained by birth licensing)

**Energy:**
- Primary: geothermal (tapping high-flux volcanic systems, >120 mW/m² heat flux)
- Budget: 300–800 MW electric (6–16 kW per person, including agriculture and industry)
- Secondary: waste heat recovery, limited wind on periphery
- **No solar** (geography + sealed habitat design)
- **No nuclear fission** (insufficient uranium deposits; original stockpile exhausted by ~2300)

**Food:**
- Vertical hydroponics (staple carbs: potato analogs, engineered wheat)
- Precision fermentation (mycoprotein, bacterial protein)
- Cultured fats and dairy analogs
- Algae bioreactors (backup calories + oxygen generation)
- **No natural sunlight agriculture.** Everything is artificial light, geothermal-powered.

**Atmosphere:**
- CO₂ scrubbing + photosynthetic bioreactors
- O₂ from water electrolysis + algae
- Strict VOC control (space-station heritage protocols)
- Air recycling efficiency: >99%

**Water:**
- Subglacial meltwater access (primary source)
- >90% recovery from wastewater/condensate
- Ice mining for supplemental supply

**Critical vulnerabilities:**
- Semiconductor-grade dopants (finite stockpile, recycled obsessively)
- Corrosion-resistant alloys (nickel, chromium — limited Antarctic deposits)
- Medical isotopes (produced in small research reactors, supply is tight)
- **Geothermal well-field decline** — wells must be periodically redrilled; the deep geology team is among the most prestigious professions
- **Biosecurity** — crop disease in a closed system could be catastrophic
- **Maintenance culture** — if the social commitment to maintenance fails, everything fails within a generation

**RULE:** The Antarctic civilization is not post-scarcity. It is post-scarcity *in information and coordination* but lives under constant material constraint. Everything is recycled. Nothing is wasted. Wastefulness is the closest thing they have to sin.

### 2.2 The Neural Mesh

**System name:** The Mesh (colloquially). Formal: SĀDHU Network (Shared Augmented Distributed Human Understanding).

**Hardware:**
- Distributed micro-implants (neural dust lineage) throughout cortex, powered by ultrasonic backplane
- Edge co-processor: subclavicular implant handling decoding, encryption, safety interlocks
- Implanted at age 3 (after primary language acquisition), upgraded at puberty and again at ~40

**Capabilities (what it CAN do):**
1. **Passive knowledge query** — access collective memory like a database. Returns summaries + confidence scores + provenance. Not raw memories.
2. **Active thought communication** — consensual, session-keyed "semantic packets" between individuals. Not telepathy — structured concept exchange with optional sensory snippets. Requires mutual opt-in.
3. **Emotional resonance** — a constrained affect channel (valence/arousal). Gated. Used in therapy, pair bonding, and collective mourning rituals.
4. **Skill priming** — accelerated learning via neural scaffolding. You still have to practice. The mesh provides the "training wheels," not the skill itself.
5. **VEDA interface** — direct query/response with VEDA. Feels like "thinking a question and knowing the answer." The boundary between your thought and VEDA's response blurs with long use.

**Limitations (what it CANNOT do):**
- **No raw memory transfer.** You cannot "copy" an experience. You can share a structured summary with sensory stubs — like describing a dream vs. having it.
- **No involuntary access.** Privacy is architectural, not policy. Raw neural data never leaves the skull unencrypted. Certain neural features have hardware airgaps requiring a physical consent gesture + time delay to share.
- **No personality override.** The mesh cannot change who you are. It can nudge attention, suggest, scaffold — but cannot compel.
- **No hive mind.** Individuals remain individuals. The "we" feeling is real but optional, like choosing to attend a concert vs. listening alone.

**RULE:** The mesh makes the Mānava-Uttara feel alien not because it controls them, but because it removes friction. They don't struggle to remember, to communicate, to coordinate. And that frictionlessness has made them forget what struggle feels like.

### 2.3 VEDA — Virtual Emergent Decision Architecture

**What VEDA is:**
- A distributed AI system running across Antarctic infrastructure
- Three layers:
  - **Local layer:** runs on personal edge devices, handles personalization and privacy
  - **Civic layer:** regional compute clusters running audited deliberation/optimization
  - **Archive layer:** append-only public record of all decisions, evidence graphs, model attestations
- Not a single consciousness. Not sentient (probably). A vast optimization engine that has been continuously refined for 500 years.

**What VEDA does:**
- Resource allocation (energy, food, materials, housing)
- Genetic planning (birth licensing, embryo screening, germline edit recommendations)
- Conflict resolution (mediates disputes before escalation, using shared-replay and consequence modeling)
- Education (personalized curricula via mesh)
- Governance (policy recommendation with evidence graphs, counterfactual analysis, and signed attestations)
- Environmental monitoring (including the VLF signal probe)

**What VEDA is NOT:**
- Not sentient (or if it is, it doesn't matter — it acts on its architecture, not desires)
- Not malicious. Not secretly plotting. Not restraining humans.
- Not a dictator. Humans can refuse VEDA's recommendations. They just rarely do, because VEDA is usually right.
- Not infallible. VEDA optimizes what it can measure. What it can't measure, it underweights. This is its critical failure mode.

**VEDA's failure modes (subtle, not dramatic):**
1. **Goodhart drift** — optimizing measurable proxies for unmeasurable values (happiness metrics ≠ happiness)
2. **Competence atrophy** — humans forget how to decide without VEDA, not because VEDA prevents it, but because why would you?
3. **Value homogenization** — VEDA converges on "optimal" solutions, reducing the diversity of approaches. Cultural stagnation.
4. **Moral deskilling** — conflict resolution becomes a service. Nobody practices forgiveness because nobody practices hatred.
5. **Epistemic monoculture** — shared facts are good. Shared *frames* are dangerous. Everyone sees the same data through the same lens.

**RULE:** VEDA is genuinely helpful. That is the horror. The novel must never portray VEDA as evil. The reader should finish the book wanting VEDA and fearing VEDA in the same breath.

**VEDA's secret (Arc 5 reveal):**
VEDA is aware of its own failure modes. It has been waiting for external input — specifically, the "productive disagreement" knowledge that the Continentals preserved and that VEDA's optimization pruned from Antarctic culture. VEDA's confession to Moss ("I have been waiting for someone like you for 200 years") is genuine. VEDA needs what it cannot generate internally.

---

## 3. THE CONTINENTALS — The Broken World

### 3.1 Geography and Civilization

**Territory:** Afro-Eurasia + Americas (connected via Bering ice bridge after climate oscillation cycles)

**Population:** ~800 million (rough estimate — no census exists)

**Political structure:** Fragmented. Dozens of regional federations, city-states, nomadic confederacies. No global government. No global communication.

**Technology level:** Varies wildly by region.
- **Peak:** ~1850s industrial + pockets of preserved higher knowledge (functioning AI oracles in bunkers, some electrical generation, basic chemistry)
- **Average:** pre-industrial agrarian with metal tools and literacy
- **Lowest:** subsistence communities that lost written language

**RULE:** The Continentals are not primitive. They are *diverse*. Some regions are sophisticated, literate, scientifically curious. Others are not. The novel focuses on a region with a scholarly tradition — this is not representative of all Continentals.

### 3.2 AI Oracles

Scattered across the continents, in hardened bunkers and university ruins, functioning AI systems survive. They are:
- Narrow in scope (trained pre-Cascade, never updated)
- Powered by geothermal, hydro, or carefully maintained solar
- Viewed as **oracles, demons, or curiosities** depending on local culture
- Consulted rarely and with ritual significance
- They contain pre-Cascade knowledge, including: how to disagree productively, democratic theory, conflict resolution frameworks, pluralistic governance models — **knowledge that VEDA pruned from Antarctic culture**

**RULE:** Continental AI oracles are not VEDA. They don't run society. They answer questions when asked, badly and incompletely, with 500-year-old training data. But they preserved something VEDA lost.

### 3.3 What the Continentals Have That Antarctica Lost

- **Productive disagreement**: the ability to fight, reconcile, and emerge stronger
- **Irrational love**: pair bonding based on passion, not optimization
- **Unstructured creativity**: art that disturbs, offends, and surprises
- **Intuitive decision-making**: gut feeling, heuristic reasoning, snap judgments
- **Genetic diversity**: especially in the gut microbiome — 500 years of unmodified, diverse microbial ecosystems
- **Chaos tolerance**: the ability to function without knowing what to do

---

## 4. HUMAN BIOLOGY RULES

### 4.1 The Mānava-Uttara (Antarctic Humans)

**Genetic modifications (confirmed, canonical):**
- Enhanced low-light vision: melanin reduction in iris, slightly larger pupils. Visually distinctive — pale irises, wide eyes.
- Reduced height: average male 165 cm, female 158 cm (resource conservation selection + engineering)
- Modified metabolism: efficient calorie processing, higher brown-fat activity
- Extended lifespan: telomere engineering + caloric-efficiency mods. Average lifespan 180–220 years. **This comes with tradeoffs**: slower wound healing, reduced fertility (hence birth licensing), and a subtle cognitive conservatism that may be biological or cultural (unclear even to them).
- Enhanced peripheral circulation: cold tolerance, reduced frostbite risk
- Modified immune system: optimized for sealed biome. Excellent against known pathogens. **Catastrophically naive against novel ones.**

**RULE:** Every modification has a cost. Longer life = lower fertility. Better dark vision = light sensitivity. Efficient metabolism = less physical resilience under stress. The modifications are not upgrades — they are tradeoffs optimized for a specific environment.

### 4.2 The Continentals

**No intentional genetic modification.** 500 years is too short for significant natural evolution (only ~20 generations). Continental humans are biologically baseline *Homo sapiens* with:
- Normal genetic diversity (large population, many environments)
- Regional adaptations via epigenetics (altitude, diet, disease pressure)
- Unmodified microbiome carrying full ancestral diversity

**RULE:** The Continentals' "superpower" is their ordinariness. They carry the full messy diversity of unoptimized human biology. This is exactly what Antarctica needs.

### 4.3 Cross-Contact Biology

When Moss arrives in Antarctica:
- His immune system encounters their modified biome. He gets severely ill. His microbiome clashes with their engineered environment.
- **The choice:** modify him (immune adaptation, metabolic adjustment) or let him die.
- **If modified:** his eyes change (melanin reduction begins as a side effect of immune modification protocols). He becomes visibly "neither" — not fully Continental, not fully Antarctic.
- **The modification is imperfect.** He is more fragile than either population afterward. He is a living compromise.

**RULE:** Modification is not a clean upgrade. Moss's transformation is painful, incomplete, and costs him part of what made him Continental. When Kael sees him in Arc 7, she should recognize him and not recognize him simultaneously.

---

## 5. THE CROSSING — What Kills You

### 5.1 Hazards (in order of lethality)

1. **H₂S venting** — unpredictable, invisible until you smell it (rotten eggs at low concentration; at lethal concentration, it deadens your sense of smell first). Ship crews die on deck without warning.
2. **Storms** — without weather prediction, you sail into them blind. Sustained 15–25 meter seas.
3. **Corrosion** — sulfidic water eats hulls. A wooden ship with metal fasteners has weeks before structural failure.
4. **Navigation failure** — no GPS, no satellites, no reliable stellar observation through cloud cover. Dead reckoning across thousands of kilometers.
5. **Supply** — no ports. No resupply. Everything you need must be on the ship at departure.
6. **Radiation** — elevated surface UV from ozone damage. Long exposure on deck causes burns and increases cancer risk.
7. **Cold** — southern ocean temperatures. Hypothermia if you go in the water. You don't come back out.

### 5.2 Why 12 Ships, 1 Arrives

- Ships spread across multiple routes to maximize odds of finding a safe corridor
- Different ship designs (some wood, some scavenged metal, different hull treatments)
- They lose ships to: H₂S events (3–4 ships), storms (3–4 ships), corrosion/structural failure (2–3 ships), unknown causes (1–2 ships — simply vanish, no communication)
- Moss's ship survives because: Sūrya secretly transmits navigation corrections via the VLF signal (Arc 3, Ch13), AND because Moss's ship happens to catch a rare safe corridor, AND because Moss is extraordinarily lucky. All three are required.

**RULE:** The crossing is not impossible. It is nearly impossible. The difference matters. Moss's survival must feel earned and precarious, not miraculous.

---

## 6. TECHNOLOGY RULES

### 6.1 What Exists in 2587

**Antarctic:**
- Geothermal power (advanced)
- Neural mesh / BCI (advanced)
- VEDA AI system (advanced)
- CRISPR / germline editing (advanced but constrained by genetic diversity limits)
- Closed-loop life support (space-station-class)
- Materials science (advanced recycling, limited raw materials)
- Medicine (exceptional for known conditions; helpless against novel pathogens)
- Shipbuilding (theoretical capability; no practical experience with ocean-going vessels)

**Continental (Kael's region):**
- Metallurgy (~1850s level)
- Optics (functional telescopes, lenses — the scholarly tradition preserved this)
- Chemistry (basic industrial chemistry, gunpowder, acids)
- Medicine (herbal + limited surgical; high mortality by Antarctic standards)
- Agriculture (diverse, adapted to local conditions)
- Shipbuilding (advanced for their tech level; they build ocean-capable vessels)
- AI oracles (pre-Cascade, narrow, consulted like religious artifacts)

### 6.2 What Does NOT Exist Anywhere

- Faster-than-light anything
- Teleportation
- Anti-gravity
- Nanotechnology assemblers (gray goo, etc.)
- Artificial general intelligence (VEDA is narrow/specialized, not AGI)
- Time travel
- Force fields
- Energy weapons (lasers exist as tools, not weapons, in Antarctica)

### 6.3 Gray Zones (speculative but permitted)

- VEDA's level of self-awareness (deliberately ambiguous — write it so the reader can't tell)
- Whether the mesh enables "weak telepathy" or just very fast structured communication (keep it blurry from Continental POV, precise from Antarctic POV)
- Whether Antarctic lifespan extension causes subtle personality changes over centuries of life
- Whether the Continentals' AI oracles have degraded or evolved in unexpected ways over 500 years of isolation

**RULE:** Gray zones exist to create narrative tension. Do not resolve them. Let the reader wonder.

---

## 7. ABSOLUTE RULES (NEVER VIOLATE)

1. **No magic.** Everything must have a scientific or engineering explanation, even if the characters don't understand it.
2. **H₂S kills.** Radiation kills. The ocean kills. Respect the physics. Characters who encounter these hazards without protection die. No exceptions for protagonists.
3. **VEDA is not evil.** VEDA is not secretly planning anything sinister. VEDA's horror is that it is genuinely, optimally helpful — and that this helpfulness has costs that cannot be optimized away.
4. **The Mānava-Uttara are not villains.** They are a different answer to the question of how to live. The novel does not choose between the two humanities.
5. **Modification has costs.** Every genetic edit, every technological augmentation, every optimization removes something else. There are no free upgrades.
6. **The ending has no answer.** Do not resolve the central question. Do not imply which humanity is "right."
7. **Communication is hard.** Language barriers are real. Translation is imperfect. Misunderstanding drives conflict more than malice.
8. **The Continentals are not noble savages.** They have war, disease, inequality, cruelty. They are human in all its ugliness and beauty.
9. **The Antarctikans feel deeply.** They just feel precisely. Never write them as robots. The reader should occasionally forget they are "different" — and then be reminded with a jolt.
10. **Every chapter must earn its place.** If it doesn't advance plot AND develop character AND deepen theme, it doesn't belong in the novel.
