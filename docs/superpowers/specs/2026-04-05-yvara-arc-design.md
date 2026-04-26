# Yvara Arc — Full Design Spec

## Overview

Complete the Academy Director (Yvara) storyline: fix existing issues, add explicit text to match CGs, build the "Support the Academy" post-Storm system, Evening at the Academy as repeatable sexual content, and two new stages (S5–S6) culminating in three possible endings.

## 1. Immediate Fixes

### 1A. CG Filename Mismatches

The Storm gate scene code references filenames that don't match the actual files on disk. Several CGs silently fail to load.

| Code expects | File on disk | Fix |
|---|---|---|
| `cg_storm_02_lord.png` | `cg_storm_02_common_lord.png` | Rename file → `cg_storm_02_lord.png` OR update code |
| `cg_storm_02_lady.png` | `cg_storm_02_common_lady.png` | Rename file → `cg_storm_02_lady.png` OR update code |
| `cg_storm_03_dominion_lord.png` | `cg_storm_03_dominance_lord.png` | Rename file → `cg_storm_03_dominion_lord.png` OR update code |
| `cg_storm_03_dominion_lady.png` | `cg_storm_03_domination_lady.png` | Rename file → `cg_storm_03_dominion_lady.png` OR update code |

**Recommendation:** Rename files to match code, since the code naming is cleaner and consistent.

### 1B. Equalize Donation/Favor Costs (S4 Current)

Current costs are inconsistent between routes:

| Tier | Donation (devotion) | Favor (dominion) |
|---|---|---|
| 1 | 900 | 900 |
| 2 | 2,100 | 2,400 |
| 3 | 4,200 | 2,700 |
| 4 | 5,400 | 4,500 |

Equalize both routes. Proposed uniform costs:

| Tier | Cost | Devotion reward | Dominion reward |
|---|---|---|---|
| 1 | 800 | Hand on heart (bust: moved) | Turn for me (bust: back) |
| 2 | 1,600 | Kiss (bust: flustered_light) | Lingerie (bust: lingerie) |
| 3 | 2,800 | Massage (bust: warm) | Topless (bust: topless) |
| 4 | 4,000 | Happy ending (bust: yielding) | Striptease (bust: striptease) |

### 1C. Rewrite Storm Scene — Explicit Text

The Storm CGs are explicitly sexual. The text must match (tone: mix of direct-but-elegant and explicit-without-filter). Yvara's voice: controlled composure that cracks under the physical.

**CG sequence and text guidance:**

1. **cg_storm_01** (Yvara at window, rain): Keep current atmospheric setup. No changes needed.

2. **cg_storm_02b** (unbuttoning blouse): Add physical narration — her fingers on the buttons, the fabric parting, the deliberateness of it. She is deciding, not being swept away.

3. **cg_storm_02** (kiss, lord/lady variants): Direct description of the kiss — mouths, hands, the shift from standing to pressed against desk/wall. Not tentative. Both versions need the physical escalation made explicit.

4. **cg_storm_03** — Four variants, each needs a dedicated explicit scene:

   **Devotion + Lord:** She is on top (cowgirl). She sets the pace initially — controlled, measured, the way she does everything. Narrate the moment control slips: her breathing, her rhythm breaking, the sounds she stops trying to suppress. He watches her come apart above him. She does not look away.

   **Devotion + Lady:** By the fireplace, skin on skin. Intimate, warm, unhurried. Hands and mouths exploring. Narrate the heat of the fire on bare skin, fingers finding sensitive places, the specific sound she makes when the player's mouth is between her legs. Post-sex: tangled together, the fire low.

   **Dominion + Lord:** Over the desk. He bends her over her own papers. She grips the edge. Narrate depth, pace, the sound of his hips against hers, her knuckles white on the desk, the moment she stops resisting the rhythm and meets it. Her glasses fall off. She doesn't reach for them.

   **Dominion + Lady:** Oral (Yvara giving). She is on her knees — her choice, but a choice made under pressure she won't name. Narrate her mouth, the player's hands in her hair, the moment Yvara's composure dissolves into the act. The closeup framing of the CG should be described: her eyes, her mouth, her expression that is equal parts pride and surrender.

**Post-sex text (all variants):** Replace the current fade-to-black "afterward" paragraphs with body-aware narration: sweat, breathing, the specific way she reassembles herself (or doesn't). Keep dialogue sparse — Yvara uses few words after sex. What she says matters more.

**Morning After:** Mostly fine as-is. Add one physical detail: she is wearing yesterday's blouse, one button off from correct. She does not fix it.

## 2. Bust Sprite Plan

### Existing busts — current and new assignments

| Bust | Status | Current use | New use |
|---|---|---|---|
| `yvara_formal_neutral` | Exists, used | Default in all visits | Default (unchanged) |
| `yvara_formal_moved` | Exists, used | Donation tier 1 | Donation tier 1 + Support tier 1 devotion |
| `yvara_formal_flustered_light` | Exists, used | Donation tier 2 | Donation tier 2 + post-sex flush moments |
| `yvara_formal_warm` | Exists, used | Donation tier 3 | Donation tier 3 + afterglow/post-intimacy |
| `yvara_formal_yielding` | Exists, used | Donation tier 4 | Donation tier 4 + S5 dominion "resigned" moments |
| `yvara_formal_back` | Exists, used | Favor tier 1 | Favor tier 1 (unchanged) |
| `yvara_formal_lingerie` | Exists, used | Favor tier 2 | Favor tier 2 + gate intermediate steps |
| `yvara_formal_topless` | Exists, used | Favor tier 3 | Favor tier 3 + gate intermediate steps |
| `yvara_formal_striptease` | Exists, used | Favor tier 4 | Favor tier 4 + gate intermediate steps |
| `yvara_formal_kiss` | **Exists, UNUSED** | — | Evening Tier 1, romantic talk moments, gate intermediate steps |
| `yvara_formal_unbutton` | **Exists, UNUSED** | — | Evening Tier 2 (transition), "casual" in evenings, gate escalation |
| `yvara_formal_amused` | **Exists, UNUSED** | — | Greetings S3+, dry humor in talks, light remarks |
| `yvara_formal_surprised` | **Exists, UNUSED** | — | Unexpected gift reactions, vulnerability moments in talks |

### New busts needed (2 only)

| Bust | Description | Use |
|---|---|---|
| `yvara_formal_angry` | Tense expression, cold eyes, clenched jaw. Same formal outfit. | S5 Talk 1 (debt revealed), dominion confrontations, wounded pride moments |
| `yvara_formal_vulnerable` | Red-rimmed eyes, no glasses, hair slightly loosened. Same outfit but "undone". | S5 gate devotion (she has been crying), the moment the armor falls completely |

### Worker sprites
Out of scope — user will create the `yvara/` worker folder and sprites separately.

### Bust-over-background technique for gate scenes
Each gate uses a multi-step visual progression: academy/office background (blurred) + bust sprite changes → then full CG for the sexual climax. This technique is already used in Storm and should be replicated in all new gates:

**S5 Gate intermediate steps:**
- Devotion: bg academy night + `vulnerable` → `kiss` → `unbutton` → **CG sex**
- Dominion: bg academy night + `yielding` → `topless` → `striptease` → **CG sex**

**S6 Gate intermediate steps:**
- Devotion: bg academy night + `amused` → `kiss` → `unbutton` → **CG sex**
- Dominion: bg player office + `neutral` → `lingerie` → `striptease` → **CG sex**
- Mixed: bg academy night + `warm` → `unbutton` → `topless` → **CG sex**

## 3. Evening at the Academy (Repeatable, Progressive)

### Purpose
Post-Storm repeatable intimate scene. Cooldown: 3 days (already implemented).

### Tier System
Tiers unlock based on "Support the Academy" investment progression (see section 4).

| Tier | Unlocked by | Visuals | Explicit level |
|---|---|---|---|
| 1 (default post-Storm) | Storm gate fired | Bust `kiss` over academy bg | Kiss + suggestive text, clothes stay on |
| 2 | 2+ investments | Bust `unbutton` over academy bg | Undressing, heavy touching, explicit but no sex narrated |
| 3 | 4+ investments | Storm CGs (02b → 02 → 03) | Full sex scene using existing Storm CGs, new explicit text |
| 4 | All 5 investments | **New dedicated Evening CGs** | Most explicit repeatable sex, exceeds Storm in intensity |

### Evening Tier 4 CGs (new, more explicit than Storm)

| ID | Description | Why it escalates beyond Storm |
|---|---|---|
| `cg_evening_devotion_lord` | Her on her back on the library sofa, him on top/between her legs, penetration from a more graphic angle than Storm's cowgirl. She has one hand gripping the sofa arm, the other pulling him closer. Fireplace glow. Face visible, expression of lost control. | Storm was her on top, composed; here she's underneath, surrendered, more exposed |
| `cg_evening_devotion_lady` | 69 by the fireplace, or the player between Yvara's legs with fingers inside while Yvara grips her hair. Both fully nude, angle showing both bodies. Yvara's expression: mouth open, overwhelmed. | Storm lady was a static post-sex nude; this is active, graphic, both participating |
| `cg_evening_dominion_lord` | Yvara on her knees on the floor of her office (not on the desk — on the floor), oral, more graphic angle than Storm. Him in the director's chair, hand in her hair. The silk ribbon (gift callback) binding her wrists behind her back. | Storm was doggy on desk; here she's on the floor, bound, the power gap is wider |
| `cg_evening_dominion_lady` | Yvara bent over the desk, player behind using toy/fingers. Yvara's hands extended gripping the far edge, academy papers scattered on the floor. Expression: submission mixed with reluctant pleasure. | Storm was an oral closeup; this is penetrative, positionally more submissive |

### Structure per Evening visit
1. Arrival narration (2-3 lines, varies by route)
2. Brief dialogue (1 exchange, cycles through pool of 4-5 openers to avoid repetition)
3. Physical escalation appropriate to tier
4. Visuals: bust changes or CGs at appropriate moments
5. Post-intimacy resolution (1-2 lines)
6. Return to visit menu

### Text variation
Pool of 3-4 text variants per tier. Track with `yvara_evening_variant_index` cycling through.

### Tone by route
- **Devotion:** She initiates or meets halfway. Warmth. Eye contact. She says your name at a specific moment.
- **Dominion:** You direct. She complies with dignity. Tension between director authority and submission. She never begs — but her body does.

## 4. "Support the Academy" System (Post-Storm)

### Purpose
Replaces S4 donations/favors after Storm fires. Unified system for both routes. Advances narrative arc toward S5 and unlocks Evening tiers. Does NOT give immediate sexual reward (that's Evening).

### Menu integration
After Storm gate fires, visit menu replaces "Donate money" / "Buy favors" with a single **"Support the Academy"** option (both routes).

### Investment tiers

| Tier | Cost | Devotion narrative | Dominion narrative | Unlocks |
|---|---|---|---|---|
| 1 | 500 | Cover minor expenses — she is grateful, resists showing it. Bust: `moved` | Pay a small debt — she signs the receipt you prepared. Bust: `neutral` | Evening Tier 2 |
| 2 | 1,000 | Fund student supplies — she shows you the classroom after. Bust: `warm` | Clear the interest on the main loan — she hands you the creditor's letter. Bust: `surprised` | — |
| 3 | 2,000 | Replace broken equipment — she is genuinely moved. Bust: `surprised` | Restructure a payment — your name is now on the paperwork. Bust: `yielding` | Evening Tier 3 |
| 4 | 3,500 | Cover the quarterly shortfall — she cries, once, briefly. Bust: `vulnerable` | Buy the outstanding note from the creditor — you own her debt now. Bust: `angry` then `yielding` | — |
| 5 | 5,000 | Endow a permanent fund — the Academy is secure. Bust: `kiss` | Foreclose the full ledger — the Academy runs at your pleasure. Bust: `yielding` | Evening Tier 4 + S5 unlock |

**Total investment to reach S5:** ~12,000 coins across 5 tiers (spread over many days at 1/day).

### Tracking variables
- `yvara_academy_investment_tier` (0-5): highest tier completed
- `yvara_academy_investment_total` (int): total coins invested post-Storm
- `yvara_academy_investments_count` (int): number of individual investments made

### One investment per day
Same cooldown as current system. Uses existing `yvara_s4_finance_last_day`.

## 5. Stage 5: "The Breaking Point"

### Entry condition
`yvara_academy_investment_tier >= 5` AND `yvara_affection >= 73`

### Narrative
The investment has revealed the full scale of the problem. Your money held things together, but the underlying structure is failing. External creditors, declining enrollment, a building that needs repairs the budget can't cover. Yvara has been holding this together with willpower and your coin, and both are running out.

This is NOT a discovery — the player has been funding the problem for stages. This is the moment where patches stop working.

### 3 Talks

**Talk 1: "The Real Number"**
Yvara finally shows you the full ledger — not the version she shows creditors, the real one. The Academy owes more than either of you expected.
- Devotion: She shows you because she trusts you. The vulnerability is real. Bust: `vulnerable`
- Dominion: You already suspected. You tell her to show you, and she does, because she no longer has the leverage to refuse. Bust: `angry` → `yielding`
- Choice affects `yvara_devotion` / `yvara_dominion` (+3-5)

**Talk 2: "What It Costs Her"**
A conversation about what the Academy means to her. Not abstract — specific. The student who arrived illiterate and now teaches. The curriculum she spent six years building. Losing this would unmake her.
- Devotion: Connect with her passion. Bust: `moved` → `warm`
- Dominion: Let her talk, then make clear that emotion is leverage. Bust: `warm` → `surprised` (she realizes what you're doing)
- Choice affects `yvara_devotion` / `yvara_dominion` (+2-4) and `yvara_affection` (+3)

**Talk 3: "The Offer"**
The player makes their move:
- Devotion: "I will save the Academy. No conditions. But I want you in my life — not as a transaction." Bust: `kiss`
- Dominion: "I can make the debt disappear. You know what it costs." Bust: `angry` → long pause → `yielding`
- Mixed options available that lean both ways
- Major stat impact: `yvara_devotion` or `yvara_dominion` (+5-8)

### 2 Remarks
Observations about physical changes in the Academy (fewer students, older materials, Yvara working later hours). Bust: `amused` for deflection attempts, `neutral` when she drops the act.

### Gate Scene: "The Bargain"
Triggers after all 3 talks + affection >= 80.

**Setup:** Night. The Academy is empty. She asked you to come — that alone is significant.

**Visual progression (bust-over-background → CG):**

**Devotion:**
1. Academy bg (blur) + bust `vulnerable` — she has been crying
2. Bust → `kiss` — she reaches for you
3. Bust → `unbutton` — clothes start coming off
4. **CG: sex scene**

**Dominion:**
1. Academy bg (blur) + bust `yielding` — she has signed
2. Bust → `topless` — you tell her to undress
3. Bust → `striptease` — she obeys
4. **CG: sex scene**

### S5 Gate CGs

| ID | Description | Narrative text |
|---|---|---|
| `cg_s5_devotion_lord` | Sex standing against the library bookshelf. He holds her up, her legs around his waist. Books fallen to the floor. Her eyes closed, gripping his shoulders, expression of need more than pleasure. Visible penetration. Single lamp lighting. | "She doesn't kiss you — she grabs you. Hands on your shoulders, nails digging in. When you lift her against the shelves the books fall and neither of you cares. She wraps her legs around you and guides you inside with her hand, no words, eyes shut. The first thrust draws a sound that isn't quite pleasure — it's relief." |
| `cg_s5_devotion_lady` | Yvara on her back on the floor by the fireplace, player on top, kissing her neck while fingers inside her. Yvara has one hand over the player's hand (guiding), the other gripping the rug. Wet eyes, not sadness but release. | "She lies back without being asked and pulls you down with her. Her hand guides yours between her legs with an urgency she doesn't try to disguise. When your fingers find her, her back arches against the floor and the sound she makes is more vulnerable than anything she's told you in words." |
| `cg_s5_dominion_lord` | Yvara on her back on her own desk, legs open, him standing between them. Explicit penetration. The signed papers visible under her back. Glasses on the floor. Expression: broken pride, not humiliation — acceptance. Hands gripping desk edge. | "You bend her over the same papers she just signed. She doesn't resist — you took her arguments half an hour ago. When you enter, her hands find the desk edge and grip. Her glasses fall. You take her face and make her look at you. She does. No defiance. No submission. Just the certainty that this is the price, and she's paying it." |
| `cg_s5_dominion_lady` | Yvara kneeling between the player's legs. Player seated in the director's chair. Oral. Player's hand in Yvara's hair, other on armrest. Yvara's hands on the player's thighs. Signed contract visible on desk beside them. | "You point at the chair — her chair — and sit in it. She understands without being told. She kneels between your legs with the same precision she applies to everything. Her mouth finds you and works with the deliberate competence of someone who has decided that if she's doing this, she'll do it well. Your hand closes in her hair and she doesn't pull away." |

## 6. Stage 6: "The Arrangement"

### Entry condition
S5 gate fired AND `yvara_affection >= 88`

### Narrative
The new reality. Yvara's relationship with the player has crystallized into one of three forms depending on accumulated stats.

### 2-3 Talks

**Talk 1: "The First Day" (dominion/mixed only)**
Yvara appears at your establishment. Uncomfortable, proud, but present. Bust: `angry` (dominion) or `amused` (mixed)
- Dominion: She obeys. You define the terms of her work.
- Mixed: She came voluntarily. The terms are negotiated, not imposed.

**Talk 1 alt: "The Visit" (devotion pure)**
She visits your establishment — not to work, but to see you. She observes your workers, your operation. Offers a professional opinion you didn't ask for. It's good advice. Bust: `amused`

**Talk 2: "The Two Lives"**
The cost of running the Academy AND being involved with you (and working for you, if applicable). She is tired but won't admit it. Bust: `warm` (devotion), `neutral` with cracks (dominion)
- Choices define how much you push or protect her

**Talk 3: "What Remains"**
The defining conversation. Bust shifts through the scene:
- Devotion: What they have is real. Not a transaction, not an arrangement. `warm` → `kiss`
- Dominion: She has accepted her place. Whether she keeps her dignity depends on prior choices. `yielding` → `vulnerable` or `neutral` depending on player's approach
- Mixed: The romance is real, but so is the work arrangement. `amused` → `kiss`

### Gate Scene: "The New Order" (arc finale)
The longest, most explicit scene of the arc.

**Visual progression (bust-over-background → CG):**

**Devotion:**
1. Academy bg night + bust `amused` — relaxed, intimate opening
2. Bust → `kiss` — she initiates
3. Bust → `unbutton` — natural undressing
4. **CG: sex scene (the most beautiful of the arc)**

**Dominion:**
1. Player office bg + bust `neutral` — she arrives in your space
2. Bust → `lingerie` — you tell her what to wear
3. Bust → `striptease` — she strips for you
4. **CG: sex scene (the most intense of the arc)**

**Mixed:**
1. Academy bg night + bust `warm` — familiar, comfortable
2. Bust → `unbutton` — the director undresses
3. Bust → `topless` — half authority, half lover
4. **CG: sex scene (the duality captured)**

### S6 Gate CGs

| ID | Description | Narrative text |
|---|---|---|
| `cg_s6_devotion_lord` | Academy bed (white sheets), cowgirl, hands intertwined over his chest. Both nude. She looks into his eyes and smiles — genuinely, during sex. Moonlight through the window. The most visually beautiful CG of the arc. | "She rides you with the slowness of someone who is no longer in a hurry for anything. Your hands find each other and intertwine on your chest. When the rhythm intensifies she doesn't close her eyes — she watches you, and for the first time in all the time you've known her, Yvara smiles without reservation. The orgasm reaches her without ceremony. She doesn't hide it." |
| `cg_s6_devotion_lady` | Both in bed, Yvara underneath, player kissing her while their bodies move together. Legs intertwined, hands on each other's faces. Nude. Expressions of absolute intimacy — eyes open, looking at each other. | "There's no urgency this time. You move together with the familiarity of bodies that already know each other. She kisses you while her hand finds you and yours finds her. The sounds you make blend together. When you both come it's almost at the same time, and she says your name as if she's learning it again." |
| `cg_s6_dominion_lord` | Player's office. Yvara wearing only a choker/collar he gave her. On her back on HIS desk (not hers), him between her legs, aggressive penetration. Her hands above her head, wrists crossed as if bound (but voluntary — she puts them there). Expression: surrendered, lips parted. | "You sit her on your desk — yours, not hers — and she opens her legs without being asked. The only thing she's wearing is the choker you gave her. When you enter, she crosses her wrists above her head and leaves them there. You didn't tell her to. She knows what you want before you ask. That's what you've built." |
| `cg_s6_dominion_lady` | Player's office. Yvara with collar, kneeling, player seated in her work chair. Explicit oral. Player holds Yvara's chin with one hand, controlling rhythm. Yvara's hands behind her back (voluntary submission). | "She kneels without being looked at. Hands behind her back, chin raised, waiting. You take her face and set the rhythm with your hand. Her mouth obeys with the same discipline she used to apply to running the Academy. The difference is that discipline is yours now." |
| `cg_s6_mixed_lord` | Academy at night. Yvara wearing her director's blouse open (nothing underneath), skirt hiked up. Sex on the library sofa. He removes her glasses gently while inside her. The duality: half-dressed as director, half-nude for him. | "You take her glasses off with your free hand and set them on the table. She lets you. Under the director's blouse she wears nothing — you've suspected for weeks and she knows it. The skirt is at her waist and you're inside her and she is still Yvara: the director, the woman who runs an academy, the woman who fucks the owner of the business keeping her afloat. All at once." |
| `cg_s6_mixed_lady` | Academy at night. Yvara with blouse open, skirt hiked, glasses still on. On her back on the desk, player on top kissing her chest while fingers between Yvara's legs. The duality: academy papers still neatly stacked beside her. | "She hasn't taken off her glasses. You didn't ask her to. The blouse is open but you haven't removed it — just parted it. The skirt is at her waist and your fingers are inside her and she still has her glasses on and somehow that makes everything more obscene. Director Yvara, legs open on top of her own quarterly reports." |

## 7. Endings and Mechanical Rewards

### Three endpoints (determined by `yvara_devotion` vs `yvara_dominion` balance after S6 gate)

#### A. Devotion Pure (devotion > dominion by significant margin)
- **Narrative:** Romance. She keeps the Academy. She keeps her independence. She loves you.
- **Yvara is NOT a worker.** She remains an independent NPC.
- **Mechanical reward:**
  - Yvara appears in random events at any building (flavor events, small bonuses)
  - Permanent discount on Academy tuition/courses
  - Access to improved laboratory or advanced training options
- **Trait on Yvara (NPC):** "Academy Director — Your Partner" (tracks relationship for event conditions)

#### B. Dominion (dominion > devotion by significant margin)
- **Narrative:** She works for you. The Academy still runs, but you own it. She serves in your establishment and teaches at the Academy.
- **Yvara IS a worker.** Added to worker pool.
- **Worker traits:**
  - "Bound by Debt" — energy regen -2 (runs Academy during the day), rebelliousness starts higher, joy penalty
  - High base skills (Charm, Service, Clever, relevant sex skills)
- **Mechanical reward:**
  - Free training sessions (limited per week)
  - Academy costs reduced (you own it)
  - Yvara as a high-skill worker

#### C. Mixed (romance exists but dominion is significant)
- **Narrative:** She loves you. She also works for you some days. Not fully comfortable but she chose it.
- **Yvara IS a worker** (part-time).
- **Worker traits:**
  - "Reluctant Arrangement" — energy regen -2, joy not penalized as harshly as dominion. Occasional days absent (Academy duties).
- **Mechanical reward:**
  - Some free training sessions
  - She appears in events when not working
  - Worker availability: ~4-5 days per week

### Yvara as Worker — General Notes
- Worker folder: `yvara/` (created by user separately)
- Worker gender: female
- Unique: true
- Base skills: high Charm (51), Service (41), Clever (41), plus sex skills matching CG content

## 8. Asset Summary

### CGs

| Type | Count | Details |
|---|---|---|
| Existing (Storm, reused) | 7 | Used in Evening Tiers 1-3 |
| Evening Tier 4 (new) | 4 | devotion lord/lady + dominion lord/lady |
| S5 Gate (new) | 4 | devotion lord/lady + dominion lord/lady |
| S6 Gate (new) | 6 | devotion lord/lady + dominion lord/lady + mixed lord/lady |
| **Total new CGs** | **14** | |

### Busts

| Type | Count | Details |
|---|---|---|
| Existing, already used | 9 | neutral, moved, flustered_light, warm, yielding, back, lingerie, topless, striptease |
| Existing, currently unused — now integrated | 4 | kiss, unbutton, amused, surprised |
| New busts needed | 2 | angry, vulnerable |
| Worker sprites | Out of scope | User creates separately |
| **Total new busts** | **2** | |

## 9. Variable Summary

### New variables needed:
```
default yvara_academy_investment_tier = 0      # 0-5, highest "Support the Academy" tier
default yvara_academy_investment_total = 0     # Total coins invested post-Storm
default yvara_academy_investments_count = 0    # Number of investments made
default yvara_evening_tier = 1                 # Current Evening explicitness tier (1-4)
default yvara_evening_variant_index = 0        # Cycles through text variants
default yvara_s5_talks_done = []               # S5 talk IDs
default yvara_s5_remarks_done = []             # S5 remark IDs
default yvara_s5_gate_fired = False            # S5 gate scene triggered
default yvara_s6_talks_done = []               # S6 talk IDs
default yvara_s6_gate_fired = False            # S6 gate / arc finale triggered
default yvara_ending_route = ""                # "devotion" / "dominion" / "mixed"
default yvara_is_worker = False                # True after dominion/mixed ending
```

### Modified stage thresholds:
```python
def yvara_recalculate_stage():
    # Existing stages 1-4 unchanged
    # Stage 5: requires S4 gate + investment tier 5 + affection >= 73
    # Stage 6: requires S5 gate + affection >= 88
```

## 10. Out of Scope

- Creating the actual CG image files (art direction descriptions provided above)
- Creating the new bust image files (`angry`, `vulnerable`) — descriptions provided
- Yvara worker folder and sprites (user handles separately)
- Changes to Academy building mechanics (courses, tuition)
- Changes to the Library Quest (intentionally separate — not a gate for Yvara's arc)
- Changes to the alchemy laboratory system
- Existing S1-S4 talk/remark content (unchanged)
- Devotion pure random events content (framework only — event pool written separately)

---

END OF SPEC
