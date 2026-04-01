# Academy Library Quest — Redesign Spec

## Problem

The current mini-game has three core issues:
1. **The puzzle isn't fun** — spelling "MANAGE" letter by letter across 7 stages feels bureaucratic
2. **The prose is dry** — heavy on institutional jargon, light on personality
3. **No real stakes** — you can't fail meaningfully, just retry until you get it right

## Design Goals

- Compact the quest from 7 stages to **3 acts + prologue** (3-4 visits minimum)
- Each visit should feel **distinct** — no repeating the same puzzle type
- **Humor seco** in narration: the library as a silent, obstinate character
- **Soft stakes**: failure costs time (lose the day); repeated failure nudges toward the paid lattice item
- **Lattice shortcut**: purchasable item that auto-solves the cipher at any point post-prologue

## Structure

### Prologue (Visit 0) — "The Gap"

**Purpose:** Setup. Discover the manual exists, is sealed, was hidden deliberately.

**Flow:**
1. Narrator establishes the library atmosphere (sensory details, dry humor)
2. Player finds the gap in the shelves — the manual should be here but isn't
3. A clerk (non-speaking, communicates via gestures and signs) points toward the restricted catalog
4. Player finds a routing slip: the manual has an embossed wax seal, 6-letter token required
5. Marginalia from a previous manager who failed ("Day five. I've tried MASTER, GOVERN, DIRECT, and STEWARD. None have six letters.")
6. First clue: the routing slip's margin shows position 1 = M
7. Mention that cryptographer's lattices exist at the Elite Emporium

**Exits with:** `academy_lib_stage = 1`, hint_a flag set (M at position 1)

**No puzzle. Pure narrative setup.**

### Act 1 (Visit 1) — "The Paper Trail"

**Purpose:** Gather clues through an observation/deduction choice.

**Flow:**
1. Narrator: you return to dig deeper into the catalog system
2. The player chooses HOW to investigate (2 paths, both succeed but yield narration differently):
   - "Search the archive desks" — methodical, slow, rewarding
   - "Follow the margin notes" — following the trail of the failed manager
3. Both paths reveal, through narrated text, the same core clues:
   - Position 3 = N, Position 5 = G (embedded in narrative)
   - Positions 2 and 4 share the same vowel
4. **The deduction choice:** Based on what they've read, the player must pick which vowel fills positions 2 and 4:
   - A (correct) / E / O
   - **Correct:** Advance. Narrator confirms. Player now knows M-A-N-A-G-?
   - **Wrong:** Lose the day. But gain a consolation clue: "At least now you know it's not [wrong vowel]." Next visit, the wrong option is removed.
5. After correct deduction: a final clue surfaces — position 6 = E

**Exits with:** `academy_lib_stage = 2`, all letter hints set, ready for seal

**Stakes:** Wrong vowel = lose the day, but narrowed options next time. Maximum 2 wasted days on this act.

### Act 2 (Visit 2+) — "The Seal"

**Purpose:** Input the token to open the manual.

**Flow:**
1. The clerk leads you to the proving desk. The wax seal sits under a lamp.
2. **Input phase** — three options always available:
   - "Use the lattice" (if in inventory) → auto-solve, skip to success
   - "Speak the token" → `renpy.input()`, validate against "MANAGE" (also accept "MANAGER" with a corrective nudge)
   - "Step back" → leave, come back another day
3. **Failure escalation (per visit):**
   - Attempt 1 fail: Dry narrator line. Retry immediately.
   - Attempt 2 fail: Narrator mentions the Elite Emporium lattice. Retry immediately.
   - Attempt 3 fail: Clerk collects the seal. Kicked out for the day.
4. **Success:** The seal opens. Transition to epilogue.

**Stakes:** 3 attempts per day. Lattice mentioned on 2nd fail as escape valve.

### Epilogue (automatic after success)

**Purpose:** Payoff. The manual opens, training unlocked.

**Flow:**
1. The binder opens — inside is practical instruction, not magic
2. Marginalia from the previous manager who gave up: "If you're reading this, you're better than me. Or richer."
3. Training interactions unlocked notification
4. Return to academy menu

## Recurring Menu (Post-Prologue)

Every library visit after the prologue shows:
- "Keep investigating" → continues current act
- "Attempt the seal" → jumps to Act 2 (input/lattice)

This lets players who already know the answer (or bought the lattice) skip ahead.

## The Lattice Item

- Sold at Elite Emporium (already exists in current implementation)
- When acquired: notification that it can be used at the library seal
- In Act 2: appears as first menu option "Use the lattice" — auto-solves
- Can be used from Act 1 onward via "Attempt the seal" menu → lattice option in Act 2

## Narrative Tone

**The library as silent character:**
- Sensory: dust, varnish, ink, creaking shelves, lamp oil
- The clerk: never speaks, communicates via gestures, signs, and pointed looks
- Marginalia: notes from a previous manager who failed — comic relief and subtle hints

**Narrator voice:**
- Dry humor, observational
- Short punchy sentences mixed with longer descriptive ones
- Has opinions about what the player is doing
- Examples:
  - "The library doesn't care about your schedule."
  - "The wax doesn't reject you dramatically. It simply doesn't open, which is worse."
  - Clerk: "points at a sign without looking up. The sign says: 'One consultation per day. No exceptions. No tears.'"

**Marginalia voice (previous manager):**
- Increasingly desperate/funny across acts
- Prologue: analytical ("Position 1 seems to be M. I'll crack this by Tuesday.")
- Act 1: frustrated ("Day five. Tried MASTER, GOVERN, DIRECT. None have six letters. Need sleep.")
- Act 2: defeated ("If you're reading this, you're better than me. Or richer. The Emporium sells lattices.")

## Technical Details

### Variables (unchanged from current)
- `academy_lib_stage`: 0 (not started) → 1 (prologue done) → 2 (act 1 done) → 3 (act 2 reached) → done
- `academy_lib_last_visit_total_days`: prevents multiple visits per day
- `store.event_flags["academy_lib_manual_found"]`: the unlock flag (unchanged)

### Event Flags
- `academy_lib_started`: set after prologue
- `academy_lib_hint_a`: M at position 1 (prologue)
- `academy_lib_hint_b`: N at 3, G at 5 (act 1)
- `academy_lib_hint_c`: E at 6, vowel match (act 1)
- `academy_lib_vowel_wrong_X`: tracks which wrong vowel was picked (for removing options)
- `academy_lib_ready_decrypt`: all clues gathered (end of act 1)
- `academy_lib_decrypt_done`: token accepted (act 2)
- `academy_lib_manual_found`: training unlocked (epilogue)
- `academy_lib_lattice_acquired`: lattice item in inventory

### Functions (mostly unchanged)
- `academy_lib_cipher_accept(guess)`: validates input (keep current logic)
- `academy_lib_has_cipher_lattice()`: checks inventory (keep current logic)
- `academy_lib_ensure_event_flags()`: safety init (keep)
- `academy_lib_today()` / `academy_lib_mark_visit_consumed()`: day tracking (keep)

### Compatibility
- The unlock flag `academy_lib_manual_found` is unchanged — no impact on worker_interactions.rpy or worker_training.rpy
- `persistent.academy_lib_quest_completed_once` kept for cross-save tracking
- Players mid-quest with old stages: stages 0-3 map to new prologue/act1, stages 4-5 map to act2. A migration block at the top handles this.

## Out of Scope
- Changes to the training interaction flow (worker_training.rpy)
- Changes to the lattice item in the shop
- New images or visual assets
- Changes to the academy building data
