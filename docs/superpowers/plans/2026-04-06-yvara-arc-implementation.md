# Yvara Arc Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete Yvara's storyline from post-Storm through two new stages to three endings, fix existing CG/cost issues, add explicit text, and build the Evening and Support the Academy repeatable systems.

**Architecture:** New Yvara content goes in a dedicated `game/scripts/yvara/yvara_arc.rpy` file to avoid bloating `script.rpy` further (~10k lines already). Existing labels in `script.rpy` that need rewriting (Storm scene, Evening, donations/favors) are edited in-place. New variables are defined alongside existing Yvara defaults in `script.rpy`. CG filenames are fixed by renaming files on disk.

**Tech Stack:** Ren'Py script (.rpy), JSON data files, Python init blocks.

**Spec:** `docs/superpowers/specs/2026-04-05-yvara-arc-design.md`

---

## Phase 1: Immediate Fixes

### Task 1: Fix CG Filename Mismatches

**Files:**
- Rename: `game/images/yvara/cg_storm_02_common_lord.png` → `cg_storm_02_lord.png`
- Rename: `game/images/yvara/cg_storm_02_common_lady.png` → `cg_storm_02_lady.png`
- Rename: `game/images/yvara/cg_storm_03_dominance_lord.png` → `cg_storm_03_dominion_lord.png`
- Rename: `game/images/yvara/cg_storm_03_domination_lady.png` → `cg_storm_03_dominion_lady.png`

- [ ] **Step 1: Rename the four CG files**

```bash
cd game/images/yvara
mv cg_storm_02_common_lord.png cg_storm_02_lord.png
mv cg_storm_02_common_lady.png cg_storm_02_lady.png
mv cg_storm_03_dominance_lord.png cg_storm_03_dominion_lord.png
mv cg_storm_03_domination_lady.png cg_storm_03_dominion_lady.png
```

- [ ] **Step 2: Verify code references match**

Check that `script.rpy` references these exact names. The existing code at lines ~9520-9588 uses:
- `cg_storm_02_lord.png` / `cg_storm_02_lady.png` (via `_cg_02` variable using `_title`)
- `cg_storm_03_dominion_lord.png` / `cg_storm_03_dominion_lady.png` (via `_cg_03` with route suffix)

Search for any other references to the old names and update if found.

- [ ] **Step 3: Commit**

```bash
git add game/images/yvara/
git commit -m "fix: rename Yvara Storm CGs to match code references"
```

### Task 2: Equalize Donation/Favor Costs

**Files:**
- Modify: `game/scripts/script.rpy` — donation labels (~9205-9351) and favor labels (~9353-9497)

- [ ] **Step 1: Update donation costs**

In `yvara_s4_donate_money` menu (line ~9209), change costs:
- Tier 1: 900 → 800
- Tier 2: 2,100 → 1,600
- Tier 3: 4,200 → 2,800
- Tier 4: 5,400 → 4,000

In each `yvara_s4_donate_tier_N` label, update the `$ money -=` line to match.

- [ ] **Step 2: Update favor costs**

In `yvara_s4_buy_favors` menu (line ~9356), change costs:
- Tier 1: 900 → 800
- Tier 2: 2,400 → 1,600
- Tier 3: 2,700 → 2,800
- Tier 4: 4,500 → 4,000

In each `yvara_s4_favor_*` label, update the `$ money -=` line to match.

- [ ] **Step 3: Update menu text to reflect new prices**

Update all menu option strings that display the price (e.g., "(900 coins)" → "(800 coins)").

- [ ] **Step 4: Commit**

```bash
git add game/scripts/script.rpy
git commit -m "balance: equalize Yvara donation/favor costs across routes"
```

### Task 3: Rewrite Storm Scene — Explicit Text

**Files:**
- Modify: `game/scripts/script.rpy` — labels `yvara_s4_gate_scene` through `yvara_s4_gate_end` (lines ~9501-9669) and `yvara_s4_morning_after` (lines ~9672-9699)

- [ ] **Step 1: Rewrite `yvara_s4_gate_devotion` (lines ~9519-9581)**

Replace the current fade-to-black text. The scene must match the CGs:
- cg_storm_02b (unbuttoning): narrate her fingers on buttons, the deliberateness
- cg_storm_02 (kiss): direct physical description of mouths, hands, escalation
- cg_storm_03 devotion lord (cowgirl): explicit sex — she sets pace, loses control, sounds she stops suppressing, orgasm described
- cg_storm_03 devotion lady (fireplace nude): explicit sex — hands and mouths exploring, fingers finding sensitive places, oral, tangled post-sex

Tone: direct-but-elegant mixed with explicit. Yvara's composure cracks under the physical. Sparse dialogue — what she says after matters more.

Keep the existing choice menus and stat effects. Only rewrite the narrator/yvara lines between them.

- [ ] **Step 2: Rewrite `yvara_s4_gate_dominion` (lines ~9583-9653)**

Same approach. Match the CGs:
- cg_storm_02 (kiss): physical escalation, pressed against desk
- cg_storm_03 dominion lord (doggy on desk): explicit — depth, pace, sound of hips, knuckles white, glasses fall, she meets the rhythm
- cg_storm_03 dominion lady (oral closeup): explicit — her mouth, player's hands in hair, composure dissolving, pride and surrender

Keep existing choice menus and stat effects.

- [ ] **Step 3: Add physical detail to Morning After (lines ~9672-9699)**

After the existing text, add one detail: she is wearing yesterday's blouse, one button off from correct. She does not fix it.

- [ ] **Step 4: Playtest the Storm scene**

Load a save at Stage 4 with `yvara_s4_gate_fired = False` and all 3 S4 talks done. Trigger the gate. Verify:
- All 4 CG variants load correctly (both lord/lady × devotion/dominion)
- Text displays properly with no overflow
- Choice menus still work
- Stats update correctly

- [ ] **Step 5: Commit**

```bash
git add game/scripts/script.rpy
git commit -m "content: rewrite Yvara Storm scene with explicit text matching CGs"
```

## Phase 2: Bust Integration & Evening Rewrite

### Task 4: Wire Unused Busts Into Existing Scenes

**Files:**
- Modify: `game/scripts/script.rpy` — `yvara_visit` greeting block (lines ~7659-7682), `yvara_talk_generic` (lines ~7967-8037), and select talk/remark labels

- [ ] **Step 1: Add bust swapping to the visit greeting**

Currently the greeting at `yvara_visit` (line ~7642) shows `yvara_formal_neutral` for every visit. Add bust changes based on stage and route:

After showing the bust, before the greeting dialogue, add conditional bust swaps:
- Stage 3+ devotion greetings: show `yvara_formal_amused` or `yvara_formal_warm`
- Stage 3+ dominion greetings: keep `yvara_formal_neutral`
- Stage 4+ post-gate: show `yvara_formal_kiss` for the "Come in" greeting (devotion)

Pattern for bust swap (insert after the existing bust show block):
```renpy
if yvara_stage >= 3 and yvara_is_devotion_route():
    $ _yvara_emote = "images/yvara/yvara_formal_amused.png"
    if renpy.loadable(_yvara_emote):
        show expression _yvara_emote:
            xpos 1.03
            ypos 1.0
            xanchor 1.0
            yanchor 1.0
            yoffset 40
```

- [ ] **Step 2: Add `surprised` bust to gift reactions**

In `yvara_gift_rare_book` (line ~9939), show `yvara_formal_surprised` when she says "Where did you find this?". In `yvara_gift_poem` (line ~9994), show `yvara_formal_moved` when she reads it.

- [ ] **Step 3: Commit**

```bash
git add game/scripts/script.rpy
git commit -m "polish: wire unused Yvara bust sprites into greetings and gift reactions"
```

### Task 5: Rewrite Evening at the Academy — Tiered System

**Files:**
- Modify: `game/scripts/script.rpy` — `yvara_evening_academy` label (lines ~9702-9758)
- Modify: `game/scripts/script.rpy` — add new defaults after existing Yvara defaults (line ~7153)

- [ ] **Step 1: Add new variables**

After line ~7153 (`default yvara_good_word_peak = False`), add:

```renpy
default yvara_evening_tier = 1                 # Evening explicitness tier (1-4)
default yvara_evening_variant_index = 0        # Cycles through text variants per tier
default yvara_academy_investment_tier = 0      # 0-5, highest "Support the Academy" tier
default yvara_academy_investment_total = 0     # Total coins invested post-Storm
default yvara_academy_investments_count = 0    # Number of investments made
```

- [ ] **Step 2: Rewrite `yvara_evening_academy` with tier system**

Replace the current Evening label (lines ~9702-9758) with a tiered system. The new structure:

```renpy
label yvara_evening_academy:
    $ _total_days = calculate_total_days()
    $ yvara_evening_academy_last_day = _total_days
    $ _tier = int(getattr(store, "yvara_evening_tier", 1) or 1)
    $ _is_dev = yvara_is_devotion_route()
    $ _title = (getattr(store, "player_title", "") or "").strip().lower()

    # --- Background setup ---
    $ _academy_bg = "images/buildings/academy.png" if renpy.loadable("images/buildings/academy.png") else "images/event_bg.png"
    scene expression _academy_bg at yvara_bg_blur
    show black as yvara_bg_dim:
        alpha 0.35

    # --- Arrival (pool of openers, cycles to avoid repetition) ---
    $ _vi = int(getattr(store, "yvara_evening_variant_index", 0) or 0) % 4
    $ store.yvara_evening_variant_index = _vi + 1

    if _is_dev:
        jump yvara_evening_devotion
    else:
        jump yvara_evening_dominion
```

Then create `yvara_evening_devotion` and `yvara_evening_dominion` labels that branch by tier, each with a pool of 3-4 text variants for the opener, then escalating visuals and text per tier.

Tier 1: bust `kiss` over bg → suggestive text, clothes stay on
Tier 2: bust `unbutton` over bg → heavy touching, explicit but no sex
Tier 3: Storm CGs (02b → 02 → 03) → full sex, explicit text (new text, reused CGs)
Tier 4: Dedicated Evening CGs → most explicit text (CGs loaded if available, fallback to Storm CGs)

Each tier ends with:
```renpy
    $ yvara_affection += 2
    $ yvara_recalculate_stage()
    call yvara_check_stage_advance from _call_yvara_check_stage_advance_evening
    jump yvara_visit_menu
```

- [ ] **Step 3: Write Tier 1-2 text (bust-only tiers)**

Write the full dialogue/narration for Tiers 1 and 2, both routes, with text variant pools. These tiers use only bust sprites over background — no CGs.

Tier 1 devotion example variant:
```renpy
    # Show kiss bust
    $ _bust = "images/yvara/yvara_formal_kiss.png"
    if renpy.loadable(_bust):
        show expression _bust:
            xpos 1.03 ypos 1.0 xanchor 1.0 yanchor 1.0 yoffset 40
    narrator "She meets you at the door. The building is quiet."
    yvara "You came."
    narrator "She kisses you. Not long, not desperate — but definite."
    narrator "The evening is short. Neither of you pushes it further tonight."
```

Tier 2 devotion example variant:
```renpy
    # Show unbutton bust
    $ _bust = "images/yvara/yvara_formal_unbutton.png"
    if renpy.loadable(_bust):
        show expression _bust:
            xpos 1.03 ypos 1.0 xanchor 1.0 yanchor 1.0 yoffset 40
    narrator "Her blouse is already loosened when you arrive. She does not explain."
    narrator "Your hand finds the opening. Her breath catches."
    narrator "Hands move. Mouths follow. Clothing shifts but does not come off entirely."
    yvara "Not yet."
    narrator "She says it like a promise, not a refusal."
```

- [ ] **Step 4: Write Tier 3 text (reuses Storm CGs)**

Full explicit sex scene text for both routes, reusing Storm CG sequence. This text should be DIFFERENT from the Storm scene text — same CGs, new narration describing a different encounter (not the first time anymore — familiarity, comfort, less surprise).

- [ ] **Step 5: Write Tier 4 text (dedicated Evening CGs)**

Full explicit sex scene text for both routes, more intense than Tier 3. References the new Evening CGs with fallback to Storm CGs if files don't exist yet:

```renpy
    $ _cg = "images/yvara/cg_evening_devotion_lord.png" if _title != "lady" else "images/yvara/cg_evening_devotion_lady.png"
    if not renpy.loadable(_cg):
        # Fallback to Storm CG
        $ _cg = "images/yvara/cg_storm_03_devotion_lord.png" if _title != "lady" else "images/yvara/cg_storm_03_devotion_lady.png"
    if renpy.loadable(_cg):
        window hide
        scene expression _cg
        pause
        window show
```

- [ ] **Step 6: Commit**

```bash
git add game/scripts/script.rpy
git commit -m "content: rewrite Evening at the Academy with 4-tier progressive system"
```

## Phase 3: Support the Academy System

### Task 6: Build "Support the Academy" Post-Storm Investment System

**Files:**
- Create: `game/scripts/yvara/yvara_arc.rpy` (new file for all post-Storm Yvara content)
- Modify: `game/scripts/script.rpy` — `yvara_visit_menu` (line ~7685) to add new menu option

- [ ] **Step 1: Create the new file with the Support the Academy system**

Create `game/scripts/yvara/yvara_arc.rpy`. This file will contain:
- Support the Academy labels
- S5 content (Task 8)
- S6 content (Task 9)
- Ending resolution (Task 10)

Start with the Support the Academy investment system:

```renpy
# yvara_arc.rpy — Yvara post-Storm arc content
# Support the Academy, Stage 5, Stage 6, Endings

label yvara_support_academy:
    $ _total_days = calculate_total_days()
    $ _tier = int(getattr(store, "yvara_academy_investment_tier", 0) or 0)
    $ _is_dev = yvara_is_devotion_route()
    $ _academy_bg = "images/buildings/academy.png" if renpy.loadable("images/buildings/academy.png") else "images/event_bg.png"

    # Tier progression menu
    if _tier >= 5:
        narrator "You have done everything you can for the Academy's finances. What remains is the conversation that follows."
        jump yvara_visit_menu

    jump expression "yvara_support_tier_{}".format(_tier + 1)
```

Then write each tier label (`yvara_support_tier_1` through `yvara_support_tier_5`) with:
- Cost check and deduction
- Route-specific narration and bust changes
- Variable updates (`yvara_academy_investment_tier`, `_total`, `_count`)
- Evening tier unlocks at tiers 1, 3, 5
- Finance cooldown using existing `yvara_s4_finance_last_day`

- [ ] **Step 2: Write all 5 investment tier scenes**

Each tier has devotion and dominion variants with appropriate bust sprites as specified in the design spec:

Tier 1 (500 coins): Devotion bust `moved`, Dominion bust `neutral`
Tier 2 (1,000 coins): Devotion bust `warm`, Dominion bust `surprised`
Tier 3 (2,000 coins): Devotion bust `surprised`, Dominion bust `yielding`
Tier 4 (3,500 coins): Devotion bust `vulnerable`, Dominion bust `angry` → `yielding`
Tier 5 (5,000 coins): Devotion bust `kiss`, Dominion bust `yielding`

Each tier ends with:
```renpy
    $ yvara_academy_investment_tier = max(yvara_academy_investment_tier, N)
    $ yvara_academy_investment_total += COST
    $ yvara_academy_investments_count += 1
    $ yvara_s4_finance_last_day = _total_days
    # Unlock Evening tier if applicable
    if yvara_academy_investment_tier >= 1 and yvara_evening_tier < 2:
        $ yvara_evening_tier = 2
    # ... etc for tiers 3 and 5
    $ yvara_recalculate_stage()
    jump yvara_visit_menu
```

- [ ] **Step 3: Integrate into visit menu**

In `yvara_visit_menu` (script.rpy line ~7685), add the "Support the Academy" option. It should appear post-Storm (`yvara_s4_gate_fired`) and replace the donate/favor options:

After the existing favor/donate menu items (lines ~7745-7754), add:

```renpy
        "Support the Academy." if yvara_s4_gate_fired and not yvara_s5_gate_fired and yvara_s4_finance_last_day != _total_days:
            jump yvara_support_academy
        "Support the Academy." if yvara_s4_gate_fired and not yvara_s5_gate_fired and yvara_s4_finance_last_day == _total_days:
            narrator "You have already contributed today."
            jump yvara_visit_menu
```

Also hide the old donate/favor options post-Storm by adding `and not yvara_s4_gate_fired` to their conditions.

- [ ] **Step 4: Commit**

```bash
git add game/scripts/yvara/yvara_arc.rpy game/scripts/script.rpy
git commit -m "feat: add Support the Academy investment system (post-Storm)"
```

## Phase 4: New Story Content

### Task 7: Add New Variables and Update Stage Thresholds

**Files:**
- Modify: `game/scripts/script.rpy` — defaults block (line ~7153) and `yvara_recalculate_stage` (line ~7176)

- [ ] **Step 1: Add S5/S6 variables**

After the Evening/investment variables added in Task 5, add:

```renpy
default yvara_s5_talks_done = []               # S5 talk IDs
default yvara_s5_remarks_done = []             # S5 remark IDs
default yvara_s5_gate_fired = False            # S5 gate scene triggered
default yvara_s6_talks_done = []               # S6 talk IDs
default yvara_s6_gate_fired = False            # S6 gate / arc finale triggered
default yvara_ending_route = ""                # "devotion" / "dominion" / "mixed"
default yvara_is_worker = False                # True after dominion/mixed ending
```

- [ ] **Step 2: Update `yvara_recalculate_stage`**

Modify the function (line ~7176) to add S5 and S6 thresholds:

```python
    def yvara_recalculate_stage():
        aff = int(getattr(store, "yvara_affection", 0) or 0)
        gate_s3 = bool(getattr(store, "yvara_s3_gate_fired", False))
        gate_s4 = bool(getattr(store, "yvara_s4_gate_fired", False))
        gate_s5 = bool(getattr(store, "yvara_s5_gate_fired", False))
        gate_s6 = bool(getattr(store, "yvara_s6_gate_fired", False))
        inv_tier = int(getattr(store, "yvara_academy_investment_tier", 0) or 0)

        if gate_s6:
            store.yvara_stage = 7
        elif gate_s5 and aff >= 88:
            store.yvara_stage = 6
        elif gate_s4 and inv_tier >= 5 and aff >= 73:
            store.yvara_stage = 5
        elif gate_s3 and gate_s4 and aff >= 64:
            store.yvara_stage = 5
        elif gate_s3 and aff >= 51:
            store.yvara_stage = 4
        elif aff >= 31:
            store.yvara_stage = 3
        elif aff >= 16:
            store.yvara_stage = 2
        else:
            store.yvara_stage = 1
```

- [ ] **Step 3: Update `yvara_visit_menu` to route S5/S6 talks**

Add S5 and S6 talk/remark routing to the visit menu, following the same pattern as S1-S4:

```renpy
        "Talk." if _talk_free_today and _s5_talk_pending:
            jump yvara_s5_talk_router
        "Talk." if _talk_free_today and _s6_talk_pending:
            jump yvara_s6_talk_router
```

Add the pending-check variables at the top of the menu:
```renpy
    $ _s5_talk_pending = yvara_stage >= 5 and not yvara_s5_gate_fired and len(yvara_s5_talks_done) < 3
    $ _s6_talk_pending = yvara_stage >= 6 and not yvara_s6_gate_fired and len(yvara_s6_talks_done) < 3
```

Same for remarks.

- [ ] **Step 4: Update `yvara_assess_feelings` for S5/S6**

Add stage 5 and 6 readout blocks following the existing pattern (line ~7782).

- [ ] **Step 5: Update `yvara_check_stage_advance` for S5 gate trigger**

Add the S5 gate trigger logic following the S3 pattern — when all talks done + affection threshold met, set a ready flag or jump directly.

- [ ] **Step 6: Remove the "more in future updates" notice**

The `yvara_continuation_notice_shown` check (line ~7734) should be removed or moved to post-S6 completion, since there IS content now.

- [ ] **Step 7: Commit**

```bash
git add game/scripts/script.rpy
git commit -m "feat: add Yvara S5/S6 variables, stage thresholds, and menu routing"
```

### Task 8: Write Stage 5 — "The Breaking Point"

**Files:**
- Modify: `game/scripts/yvara/yvara_arc.rpy` — add S5 labels

- [ ] **Step 1: Write S5 talk router and Talk 1 ("The Real Number")**

```renpy
label yvara_s5_talk_router:
    if "s5_t1" not in yvara_s5_talks_done:
        jump yvara_s5_talk_1
    elif "s5_t2" not in yvara_s5_talks_done:
        jump yvara_s5_talk_2
    elif "s5_t3" not in yvara_s5_talks_done:
        jump yvara_s5_talk_3
    else:
        jump yvara_talk_generic
```

Talk 1: Yvara shows the real ledger. Devotion: trust + vulnerability (bust `vulnerable`). Dominion: you demand to see it (bust `angry` → `yielding`). Include choice menus affecting devotion/dominion (+3-5).

- [ ] **Step 2: Write Talk 2 ("What It Costs Her")**

What the Academy means to her — specific (the illiterate student, the curriculum). Devotion: connect with her passion (bust `moved` → `warm`). Dominion: emotion as leverage (bust `warm` → `surprised`). Choices affect devotion/dominion (+2-4) and affection (+3).

- [ ] **Step 3: Write Talk 3 ("The Offer")**

The player makes their move. Devotion: "No conditions, but I want you." Dominion: "You know what it costs." Mixed options available. Bust: `kiss` (devotion), `angry` → `yielding` (dominion). Major stat impact (+5-8).

- [ ] **Step 4: Write S5 remarks (2)**

Observations about the Academy's decline. Bust: `amused` for deflection, `neutral` when she drops the act. Each remark gives small affection/devotion/dominion boosts.

- [ ] **Step 5: Write S5 Gate Scene — "The Bargain"**

The gate triggers when all 3 S5 talks done + affection >= 80. Two variants:

**Devotion:** bust progression `vulnerable` → `kiss` → `unbutton` → CG `cg_s5_devotion_lord/lady`. Explicit sex scene (standing against bookshelf for lord, fireplace floor for lady). Text as described in spec.

**Dominion:** bust progression `yielding` → `topless` → `striptease` → CG `cg_s5_dominion_lord/lady`. Explicit sex (desk for lord, director's chair for lady). Text as described in spec.

CG loading with fallback:
```renpy
    $ _cg = "images/yvara/cg_s5_devotion_lord.png" if _title != "lady" else "images/yvara/cg_s5_devotion_lady.png"
    if renpy.loadable(_cg):
        window hide
        scene expression _cg
        pause
        window show
```

Gate ends with `$ yvara_s5_gate_fired = True` and stage recalculation.

- [ ] **Step 6: Commit**

```bash
git add game/scripts/yvara/yvara_arc.rpy
git commit -m "content: add Yvara Stage 5 — The Breaking Point (talks, remarks, gate)"
```

### Task 9: Write Stage 6 — "The Arrangement"

**Files:**
- Modify: `game/scripts/yvara/yvara_arc.rpy` — add S6 labels

- [ ] **Step 1: Determine ending route**

Add a function to determine the ending route based on accumulated stats:

```python
init python:
    def yvara_determine_ending():
        dev = int(getattr(store, "yvara_devotion", 0) or 0)
        dom = int(getattr(store, "yvara_dominion", 0) or 0)
        diff = abs(dev - dom)
        if dev > dom and diff >= 10:
            return "devotion"
        elif dom > dev and diff >= 10:
            return "dominion"
        else:
            return "mixed"
```

- [ ] **Step 2: Write S6 talk router and Talk 1**

Talk 1 has three variants:
- "The First Day" (dominion/mixed): Yvara at your establishment. Bust: `angry` (dominion), `amused` (mixed).
- "The Visit" (devotion): She visits voluntarily, offers professional opinion. Bust: `amused`.

- [ ] **Step 3: Write Talk 2 ("The Two Lives")**

The cost of the dual existence. Bust: `warm` (devotion), `neutral` (dominion). Choices define how much you push or protect her.

- [ ] **Step 4: Write Talk 3 ("What Remains")**

The defining conversation. Bust shifts: devotion `warm` → `kiss`, dominion `yielding` → `vulnerable`, mixed `amused` → `kiss`.

- [ ] **Step 5: Write S6 Gate Scene — "The New Order" (arc finale)**

Three variants, each with bust-over-bg progression → CG:

**Devotion:** `amused` → `kiss` → `unbutton` → CG `cg_s6_devotion_lord/lady`. Most beautiful scene. She smiles during sex. Explicit text as in spec.

**Dominion:** `neutral` → `lingerie` → `striptease` → CG `cg_s6_dominion_lord/lady`. Most intense scene. Collar, surrender. Explicit text as in spec.

**Mixed:** `warm` → `unbutton` → `topless` → CG `cg_s6_mixed_lord/lady`. The duality — director clothes half-removed. Explicit text as in spec.

Gate ends with:
```renpy
    $ yvara_s6_gate_fired = True
    $ yvara_ending_route = yvara_determine_ending()
    $ yvara_recalculate_stage()
```

- [ ] **Step 6: Commit**

```bash
git add game/scripts/yvara/yvara_arc.rpy
git commit -m "content: add Yvara Stage 6 — The Arrangement (talks, gate, endings)"
```

### Task 10: Implement Ending Rewards

**Files:**
- Modify: `game/scripts/yvara/yvara_arc.rpy` — add ending resolution label
- Modify: `game/scripts/script.rpy` — `yvara_visit_menu` for post-arc state

- [ ] **Step 1: Write ending resolution label**

After S6 gate fires, the next visit triggers the ending resolution:

```renpy
label yvara_ending_resolution:
    $ _route = getattr(store, "yvara_ending_route", "") or yvara_determine_ending()
    $ store.yvara_ending_route = _route

    if _route == "devotion":
        jump yvara_ending_devotion
    elif _route == "dominion":
        jump yvara_ending_dominion
    else:
        jump yvara_ending_mixed
```

**Devotion ending:** She keeps the Academy. She keeps independence. Mark NPC relationship flag. Grant Academy discount and improved lab access.

**Dominion ending:** She becomes a worker. Add Yvara to `store.workers` with appropriate stats and "Bound by Debt" trait. Grant free training and Academy cost reduction.

**Mixed ending:** She becomes a part-time worker. Add Yvara to `store.workers` with "Reluctant Arrangement" trait. She appears in events when not working.

- [ ] **Step 2: Create Yvara worker data**

Add worker data for dominion/mixed endings. The worker JSON goes in `game/data/workers/yvara.json`:

```json
[
    {
        "name": "Yvara",
        "folder": "yvara",
        "cost": 0,
        "nsfw": true,
        "unique": true,
        "encounter_only": false,
        "monster": false,
        "procedural": false,
        "skills": {
            "Charm": 51,
            "Service": 41,
            "Clever": 41,
            "Hand": 35,
            "Oral": 38,
            "Sex": 35,
            "BDSM": 30,
            "Striptease": 40,
            "Agility": 35,
            "Homo": 32
        },
        "names_list": "western_female",
        "traits": ["Human"],
        "description": "The Academy Director. She runs an institution by day and serves your establishment by arrangement — willingly or otherwise.",
        "gender": "female",
        "comfort_desired": 5
    }
]
```

- [ ] **Step 3: Create trait definitions**

Add to `game/data/traits/traits_yvara.json`:

```json
[
    {
        "name": "Bound by Debt",
        "only_assigned": true,
        "modifiers": {
            "energy_regeneration": -2,
            "joy": -5,
            "rebelliousness": 5
        },
        "description": "Yvara works for you because she owes you everything. She runs the Academy during the day. [-2 Energy Regen, -5 Joy, +5 Rebelliousness]"
    },
    {
        "name": "Reluctant Arrangement",
        "only_assigned": true,
        "modifiers": {
            "energy_regeneration": -2,
            "joy": -2
        },
        "description": "Yvara works for you by choice — but the Academy still demands her days. [-2 Energy Regen, -2 Joy]"
    },
    {
        "name": "Academy Director — Your Partner",
        "only_assigned": true,
        "modifiers": {},
        "description": "Yvara loves you and runs the Academy independently. She appears in events across your buildings."
    }
]
```

- [ ] **Step 4: Update post-arc visit menu**

After `yvara_s6_gate_fired`, the visit menu should:
- Remove "Support the Academy" option
- Keep "Evening at the Academy" (repeatable, Tier 4 permanent)
- Keep "Talk" with generic post-arc dialogue
- Keep "Bring a gift"
- Keep "Take her measure" (updated for post-arc)
- Add "Work arrangement" (dominion/mixed only) for managing her schedule

- [ ] **Step 5: Commit**

```bash
git add game/scripts/yvara/yvara_arc.rpy game/scripts/script.rpy game/data/workers/yvara.json game/data/traits/traits_yvara.json
git commit -m "feat: implement Yvara ending rewards — worker data, traits, post-arc menu"
```

## Phase 5: Polish

### Task 11: Final Integration and Playtesting

**Files:**
- All modified files from previous tasks

- [ ] **Step 1: Verify label routing**

Ensure all `jump` and `call` targets exist. Search for any broken references:
```bash
grep -n "jump yvara_" game/scripts/yvara/yvara_arc.rpy game/scripts/script.rpy | sort
grep -n "^label yvara_" game/scripts/yvara/yvara_arc.rpy game/scripts/script.rpy | sort
```

Compare the two lists — every jump target must have a matching label.

- [ ] **Step 2: Verify `from` clause uniqueness**

Every `call ... from` in Ren'Py needs a unique `from` label. Check that new `call yvara_check_stage_advance from _call_yvara_check_stage_advance_XXX` uses unique suffixes not conflicting with existing ones.

- [ ] **Step 3: Verify CG fallback chains**

Every CG reference should have a fallback. Test with CG files missing to ensure no crashes:
- Evening Tier 4 falls back to Storm CGs
- S5 gate CGs fall back gracefully (skip the CG display)
- S6 gate CGs fall back gracefully

- [ ] **Step 4: Update `yvara_assess_feelings` for all stages**

Ensure the "Take her measure" output correctly shows S5 and S6 progress, investment tier, and ending route prediction.

- [ ] **Step 5: Playtest full arc**

Test the following path:
1. Start from a save with Academy enrolled, Yvara at Stage 4 pre-Storm
2. Trigger Storm → verify explicit text + CGs load
3. Morning After → verify
4. Evening at the Academy Tier 1 → verify bust `kiss`
5. Support the Academy × 5 investments → verify tier unlocks
6. Evening Tiers 2, 3, 4 → verify escalation
7. S5 talks (3) → verify bust changes
8. S5 gate → verify CG loading + explicit text
9. S6 talks (2-3) → verify
10. S6 gate → verify correct ending route + CGs
11. Post-arc visit → verify menu state

- [ ] **Step 6: Final commit**

```bash
git add -A
git commit -m "feat: complete Yvara arc — Storm rewrite, Evening, Support, S5, S6, endings"
```

---

END OF PLAN
