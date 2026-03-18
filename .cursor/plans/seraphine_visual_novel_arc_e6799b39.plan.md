---
name: Yvara Visual Novel Arc
overview: Design and script a ~2.5-hour visual novel arc centered on Yvara, independent proprietor of the Academy. Six stages slow the progression and multiply adult scenes. Visit interactions evolve from professional exchanges into full scenes as the relationship deepens, and each route (Devotion, Dominion, Combined) has its own adult scene sequence before the ending.
todos:
  - id: yvara-character
    content: Create Yvara's NPC data entry (not a standard worker — unique flags, 6-stage affection tracker, route trackers)
    status: pending
  - id: academy-building
    content: Add Academy building type with enrollment fee, worker training passive, and Visit Yvara access point
    status: pending
  - id: yvara-visits
    content: Write yvara_visits.json — all visit options across 6 stages, including which ones convert into full scenes after story flags
    status: pending
  - id: yvara-items
    content: Add Rare Book and Fine Wine to items.json with Yvara-specific gift reactions per stage
    status: pending
  - id: yvara-scenes-s1s2
    content: Write Stage 1-2 scenes in yvara_arc.rpy (Enrollment, Unguarded Moment, Standards, Late Hour, Ledger)
    status: pending
  - id: yvara-scenes-s3
    content: Write Stage 3 scenes (The Garden, The Favor, The Incident, After the Tour adult event)
    status: pending
  - id: yvara-scenes-s4
    content: Write Stage 4 scenes (The Storm full adult event × 3 routes, The Morning After)
    status: pending
  - id: yvara-scenes-s5
    content: Write Stage 5 scenes (Her Secret, The Agreement, The Inquisitor, route-specific adult scene 2 × 3 routes)
    status: pending
  - id: yvara-scenes-s6
    content: Write Stage 6 ending scenes × 3 routes, each with full adult content and worker-join branching
    status: pending
  - id: yvara-events
    content: Write events_academy.json — 4 Academy random events + The Inquisitor Governor subplot event
    status: pending
  - id: yvara-arc-logic
    content: Wire stat tracking, 6-stage gates, cooldown flags, visit-to-scene conversion logic, and adult unlock flags
    status: pending
isProject: false
---

# Yvara — Visual Novel Arc (Academy Route, 6 Stages)

## Core Principle: Visits Become Scenes

In Stage 1–2, visiting Yvara is a brief professional exchange. The same visit option — "Stay to Talk", "Check Progress", "Evening at the Academy" — changes qualitatively as the relationship deepens. By Stage 5, those same options are full visual novel scenes with dialogue, atmosphere, and adult content potential. This mirrors the Akabur model: the same action means something different at each level of the relationship.

Adult content does not arrive all at once. It builds:

- Stage 3 → first physical contact (tense, non-explicit)
- Stage 4 → first full adult scene (The Storm, route-split)
- Stage 4+ → repeatable soft adult content via visits
- Stage 5 → route-specific full adult scene (each route gets one)
- Stage 6 → ending adult scene (each route) + permanently repeatable

---

## Core Premise

**The Academy** is a building the player purchases access to (~8,000 gold). It is *not* the player's property — Yvara owns it and runs it. The player pays an **enrollment fee** per worker they send there for training. The Academy passively upgrades Clever/Charm skills of enrolled workers each week.

**Yvara is not waiting for the player.** She is a busy, independent professional. The player earns the right to have a real conversation with her over time. The relationship begins from zero: she sees the player as a client account, nothing more.

---

## Yvara's Profile

- Former court scholar, cast out when the Governor purged his inner circle
- Founded the Academy with everything she had left — it is her life's work and her only stability
- Personality: composed, precise, dry wit when she drops her guard, quietly furious when her competence is questioned
- Secret: she was present when the Governor signed the order that destroyed the player's family — and she has the document
- Voice: elevated archaic English at her most professional, slips into more direct speech when the armor cracks

She is never waiting. She is always already in the middle of something.

---

## Why the Player Has Leverage (Domination Route)

Since Yvara is not a worker, dominance cannot come from employment. Instead it builds through **three circumstantial levers**:

1. **Financial**: The Academy's ledger does not balance. The player, as the largest single patron, discovers this. An offer of financial backing comes with an unspoken expectation of access.
2. **Knowledge**: The player eventually learns she was there the night their family was destroyed. She knows it too. The power in that knowledge belongs to whoever chooses to use it.
3. **Dependency**: By Stage 3, she has allowed herself to need the player in ways she did not plan — and she knows it, and she cannot fully undo it.

The domination route is about the player *creating and maintaining* a position of leverage, not wielding pre-existing authority.

---

## Route System

Two tracked variables (0–100 each):

- `yvara_devotion` — respect, gifts, emotional openness, asking instead of taking
- `yvara_dominion` — leverage, financial pressure, testing limits, taking instead of asking

Derived:

- `yvara_affection = floor((devotion + dominion) / 2)` — gates stage progression

**Ending conditions (Stage 4):**

- Devotion ≥ 60, Dominion < 30 → **Route A: Partnership** (equal romance)
- Dominion ≥ 60, Devotion < 30 → **Route B: Surrender** (full domination, NSFW-gated)
- Both ≥ 40 → **Route C: Balance** (combined, best ending, unique scenes)

---

## Stage Structure (6 Stages)

```
Stage 1: Affection  0–15  | Days  1–10  | "The Client"        — she is a service provider, nothing more
Stage 2: Affection 16–30  | Days 11–21  | "The Acquaintance"  — she has noticed the player as a person
Stage 3: Affection 31–50  | Days 22–35  | "The Patron"        — something is shifting, first physical tension
Stage 4: Affection 51–63  | Days 36–48  | "The Complication"  — The Storm fires (first full adult scene)
Stage 5: Affection 64–72  | Days 49–58  | "The Admission"     — NEW: the conscious choice after The Storm
Stage 6: Affection 73–82  | Days 59–70  | "The Entanglement"  — route-specific adult scenes, stakes raised
Stage 7: Affection 83–90  | Days 71–82  | "The Threshold"     — hardcore B/C scene; Route A equivalent added
Stage 8: Affection 91–100 | Days 83+    | "Irrevocable"       — endings, full adult scenes, permanent unlock
```

Each stage-advancing story scene has a **7-day cooldown** — cannot advance more than one stage per week regardless of gold spent. This creates ~83 days minimum of engagement before an ending can fire.

---

## Visit Mechanic & Visit-to-Scene Evolution

The player accesses Yvara via **"Visit Academy"** on the map screen. Each option below is available from the stage indicated. The description column shows how the same option transforms across stages.


| Visit Option           | Unlocked              | Cooldown | Cost | What it is at unlock         | What it becomes                                                   |
| ---------------------- | --------------------- | -------- | ---- | ---------------------------- | ----------------------------------------------------------------- |
| Check Progress         | Stage 1               | 1 day    | Free | One-line professional report | Stage 4+: real conversation, adult-possible at Stage 5            |
| Ask a Question         | Stage 1               | 1 day    | 50g  | Professional answer          | Stage 3+: genuine exchange, choice-driven; becomes "Stay to Talk" |
| Bring a Gift           | Stage 1               | None     | Item | Polite formal thanks         | Stage 3+: visible emotional reaction; Stage 5+: intimate moment   |
| Stay to Talk           | Stage 2               | 2 days   | Free | Short choice, small effect   | Stage 4+: full conversation scene; Stage 5+: adult-possible       |
| Review the Ledger      | Stage 2 (Dom)         | 3 days   | Free | Financial discussion         | Stage 4+: leverage/power dynamic scene                            |
| Invite to Dine         | Stage 3               | 3 days   | 300g | Requires Restaurant owned    | Stage 4: real date scene; Stage 5+: adult-possible                |
| Evening at the Academy | Stage 4 (post-Storm)  | 3 days   | Free | Short intimate scene         | Stage 5+: explicit NSFW scene                                     |
| Private Study          | Stage 5 (Route B/C)   | 2 days   | Free | —                            | Full adult domination scene                                       |
| Morning Walk           | Stage 5 (Route A)     | 2 days   | Free | —                            | Romantic scene, adult possible                                    |
| Private Arrangement    | Stage 6 (post-Ending) | 3 days   | Free | —                            | Permanently repeatable full adult scene                           |


---

## Gift Items

Yvara reacts to gifts brought during a visit. Her reaction changes by stage and route.

- **Perfect Flower Bouquet** — Stage 1: polite thanks, nothing more. Stage 2+: visible effect. → +4 Dev, +2 Affection
- **Luxury Bonbons** — She claims not to have a sweet tooth. She is lying. → +3 Dev, +2 Affection
- **Rare Book** (new item, Shop 2, ~600g) — She reads the title, looks up at the player, says nothing. Then: *"Thank you."* No archaic register. → +8 Dev, +5 Affection
- **Fine Wine** (new item, event drop or Shop 2, ~300g) — Best used at Stage 2+ "Stay to Talk." Changes the scene tone. → +3 Dev, +2 Dom if framed correctly, +3 Affection
- **Enchanted Amulet** (existing item) — Giving it to her in Stage 3+ carries weight neither of them acknowledges aloud. → +5 Dom, +3 Affection

---

## Full Scene & Adult Content Map

---

### PROLOGUE (Fires automatically on Academy building purchase — not on first manual visit)

Scene 0 triggers as part of the building purchase flow, immediately after the Academy is bought and paid for. The player does not need to manually visit — the scene cuts directly to Yvara the moment the transaction completes. This is the first time the player sees her, and the first time the bust and office background are displayed.

**Technical hook:** A label `yvara_prologue` defined in `yvara_arc.rpy` is called from the building purchase confirmation in `building_logic.rpy` when `building_id == "academy"`. After the label returns, the "Visit Academy" option becomes available on the map screen.

**First assets needed (highest production priority — required before any other Yvara art):**

- `yvara_formal` body + `neutral` face overlay — the first image the player sees
- `bg_yvara_office` (day) — the first background the player sees

---

**Scene 0 — "The Enrollment"**

> The Academy smells of parchment and lamp oil. A woman is writing at a lectern, not looking up.

`SERAPHINE:` *"One moment."*

She finishes the line. Sets down her quill. Looks up with the composed expression of someone who has given this orientation many times.

`SERAPHINE:` *"You are the new patron. I am Yvara. I run this institution. Your workers will report each morning and leave by evening — I do not offer lodging. The fee is due at the start of each week. Do you have questions?"*

- `[A]` *"Just one. What exactly will they learn?"* → professional, she warms 1 degree, +1 Dev
- `[B]` *"No questions. I trust it is worth the price."* → she notes the tone, neutral
- `[C]` *"Several. But they can wait."* → she raises an eyebrow very slightly, +1 Dom

All three paths: she hands over the enrollment ledger. The player signs. The scene ends.
*She has already returned to writing before you reach the door.*

---

### STAGE 1 — "The Client" (Affection 0–15, Days 1–10)

*She is professional. The player is a fee. She is competent, occasionally dry, and entirely uninterested in extending interactions.*
*Available visits: Check Progress (free), Ask a Question (50g), Bring Gift.*

**Scene 1-A (after 4+ "Ask a Question" visits, Day 6+) — "The Unguarded Moment"**

The player arrives slightly early. Yvara has not heard them come in. She is scolding a cat that has walked across her papers — quietly, precisely, in the same tone she uses for everything else.

`SERAPHINE:` *(noticing the player)* *"How long have you been standing there?"*

- `[A]` *"Long enough to learn you are consistent in your standards."* → she gives a single short exhale that is almost a laugh. +3 Dev, +3 Affection
- `[B]` *"Not long. Is the cat also enrolled?"* → she looks at the cat. Then: *"It pays no fees and contributes nothing. It is therefore more academically representative than most patrons."* +2 Dev, +2 Affection
- `[C]` *"Long enough."* → she files it away. Says nothing more. +1 Dom

*This is the first time she has been anything other than professional. She reassembles herself quickly.*

**Scene 1-B (after 3+ commanding visit choices, Day 7+) — "The Question of Standards"**

She presents slow worker progress without apology. It is their workers, not her teaching.

`SERAPHINE:` *"I can accelerate certain areas if you specify a focus. I cannot make someone learn faster than their nature allows."*

- `[A]` *"What would you recommend?"* → +3 Dev (she respects the question, gives a real answer)
- `[B]` *"Then perhaps my investment should go elsewhere."* → she meets his/her eyes. *"That is your prerogative."* Does not flinch. +1 Dom
- `[C]` *"Double their hours. I will pay the difference."* → she pauses. *"...I can arrange that."* +3 Dom, costs +500g/week

---

### STAGE 2 — "The Acquaintance" (Affection 16–30, Days 11–21)

*She has noticed the player as a person. She is not sure she likes that.*
*New visits unlock: Stay to Talk (2 day cooldown), Review the Ledger (Dom path).*

**Event 2-X — "The Ledger" (Dominion trigger, fires on first "Review the Ledger" visit, Day 12+)**

The player asks to see financial records. The numbers are not catastrophic but they are uncomfortable. She knows he/she has noticed.

`SERAPHINE:` *"The Academy is in a period of... consolidation."*

- `[A]` *"I can help with that. If you want."* → +4 Dev, +4 Affection (this was not expected of him/her)
- `[B]` *"That is concerning. For my investment."* → +4 Dom, +3 Affection (she straightens — he/she has framed the leverage correctly)
- `[C]` *"Show me everything."* → +5 Dom, +3 Affection, unlocks `leverage_financial` flag

**Event 2-Y — "The Late Hour" (Devotion trigger, fires on a "Stay to Talk" visit, Day 13+)**

The player stays past closing. She finds them still there, reading.

`SERAPHINE:` *"I did not realise—"*
`PLAYER:` *"I was reading. I hope that was not an imposition."*

She glances at the book he/she chose. Something shifts.

They talk — about the book first, then about other things: ambition, loss, what people build when they have nothing left to lose. She says one true thing about herself without meaning to. She notices. She does not take it back.

+6 Dev, +6 Affection, unlocks `late_hour_flag`

---

### STAGE 3 — "The Patron" (Affection 31–50, Days 22–35)

*Something is shifting. The professional framing still exists but it no longer fits perfectly.*
*New visits unlock: Invite to Dine (300g, 3 day cooldown).*

**Scene 3-A (Devotion ≥ 14, Day 22+) — "The Garden"**

She is outside during a break, reading. She does not invite the player to sit. She does not ask them to leave.

`SERAPHINE:` *"You build all of this to bring one man down. Have you thought about what you will do after?"*

- `[A]` *"Build something worth keeping."* → +5 Dev
- `[B]` *"I have not gotten that far."* → +3 Dev (*"Honest, at least."*)
- `[C]` *"Whatever serves my purpose."* → +3 Dom (*"Yes. I suppose that is the honest answer for most."*)

+8 Affection, flag `shared_confidence`

**Scene 3-B (Dominion ≥ 14, `leverage_financial` flag, Day 22+) — "The Favor"**

The player helped with the finances. Now they mention, casually, that they would like a private tour after hours.

`SERAPHINE:` *"That is an unusual request."*
`PLAYER:` *"I like to know what I am funding."*

A beat. She closes her ledger.

`SERAPHINE:` *"...This evening, then. After the last class."*

The tour is professional. But it is private. And she gave it. Both of them know what that means.

+6 Dom, +5 Affection

**Scene 3-C (Affection 36+, neutral, Day 28+) — "The Incident"**

A student is hurt during a lesson. The player is present, acts without being asked. She watches him/her handle it: two fast decisions, clean resolution.

`SERAPHINE:` *"You did not hesitate."*
`PLAYER:` *"Neither did you."*

+5 Affection (route-neutral), +15 Reputation

---

### ADULT EVENT 1 — "After the Tour" (Stage 3, NSFW-gated, fires after Scene 3-B + 2 more visits)

The player visits again after hours on a pretext neither of them bothers to make convincing. The building is empty. She is less armored than usual.

**Route B version:** He/she moves closer than professionally warranted. She does not step back. He/she reaches out — deliberately, watching her — and adjusts the clasp on her collar. She lets him/her.

`SERAPHINE:` *"You are testing something."*
`PLAYER:` *"I am."*
`SERAPHINE:` *"...And if I asked you to stop?"*
`PLAYER:` *"Then I would stop."*

She says nothing. She does not ask him/her to stop.
→ *[NSFW: physical proximity, first real contact — not explicit yet. Consent established through silence.]*

**Route A version (fires if Devotion dominant):** Conversation in the empty library. At some point she realises the distance between them has closed without either of them deciding it. First touch: she does not move away.
→ *[Romantic tone. No explicit content. But a line was crossed.]*

**"Evening at the Academy"** unlocks as a recurring visit option after this event.

---

### STAGE 4 — "The Complication" (Affection 51–65, Days 36–50)

*The line between patron and something else is blurring. Both know it. Neither has named it.*
*"Evening at the Academy" is now available as a repeatable visit (3 day cooldown, short intimate scene, NSFW soft).*

**THE STORM EVENT (major event, all routes, Day 38+, Affection 50+)**

A storm traps both of them in the Academy overnight. No dramatic setup — simply practical. They share the space. They talk without the client-proprietor structure to hide behind.

*This is the first full adult scene. It branches hard by route:*

**Storm — Route A (Devotion ≥ 30):**
The conversation runs out of neutral territory. She says something she had not meant to. He/she responds without the careful distance they have both been maintaining. She kisses him/her first.

`SERAPHINE:` *(pulling back slightly)* *"I should not have done that."*
`PLAYER:` *"You should do it again."*

She considers this. For a long moment.
→ *[NSFW romantic scene: she is fully in control of her choices. It is gentle and certain.]*

Afterward:
`SERAPHINE:` *"I am not sure what this is."*
`PLAYER:` *"Neither am I."*
`SERAPHINE:` *"Good. I would distrust certainty at this stage."*

**Storm — Route B (Dominion ≥ 30):**
Controlled conversation until the player moves — not aggressively, but with the clarity of someone who has been patient long enough.

`SERAPHINE:` *"This was not part of any arrangement."*
`PLAYER:` *"No. It is a new one."*

She holds his/her gaze for a long moment. There is genuine resistance — not fear. Pride. And then it yields.
→ *[NSFW: power dynamic. She yields willingly, with full awareness of what she is doing.]*

Afterward she is quieter than usual. Not broken. *Settled.*

**Storm — Route C (Both ≥ 25):**
Begins as Route A: she initiates. He/she takes over from there.
→ *[NSFW: tender that becomes dominant, or dominant that becomes tender — player choices mid-scene steer it.]*

**After The Storm: "Evening at the Academy" upgrades** — the scene is now explicitly adult when the NSFW toggle is on.

**Scene 4-X (post-Storm, Day 40+) — "The Morning After"**

Brief scene, no choices. She is already at her desk when he/she wakes. Professional posture. Tea is made.

`SERAPHINE:` *"I trust you slept adequately."*

A pause that lasts slightly too long.

`PLAYER:` *"I did."*

She hands him/her the tea. Her fingers brush his/hers. Neither of them comments.

+3 Affection, sets tone for Stage 5

---

### STAGE 5 — "The Admission" (Affection 64–72, Days 49–58)

*The Storm was circumstantial — they were trapped. This is not. The player returns on an ordinary afternoon, and both of them know exactly why.*

**ADULT EVENT — "The Second Visit" (all routes, NSFW, Day 50+, Affection 64+)**

There is no pretext this time. The player arrives. She looks up and does not reach for a ledger or a progress report. She just looks.

`SERAPHINE:` *"You are not here about the Academy."*
`PLAYER:` *"No."*

A silence. She sets down whatever she was holding.

`SERAPHINE:` *"...No. I did not think so."*

**Route A:** She crosses the room. Unhurried. This is her decision and she makes it fully.
→ *[NSFW romantic scene: warmer and more certain than The Storm. The first time it happens without surprise on either side.]*

**Route B:** She does not move. She waits. She is testing whether he/she will take what the Storm established or wait for permission. He/she does not wait.
→ *[NSFW: power dynamic, more settled than The Storm. She knows what this is now and she has not left.]*

**Route C:** She moves first. He/she takes over before she finishes.
→ *[NSFW combined: the pattern they have found together. Neither surprises the other now.]*

One CG (`cg_second_visit`) — single image, the moment before. Route flavoring is dialogue only.

+8 Affection, flags `second_visit_fired` (route-tracked)

**Scene 5-A (Day 52+) — "The Habit"**

Brief non-choice scene. She mentions, without particular emphasis, that she expected the player yesterday.

`SERAPHINE:` *"You did not come yesterday."*
`PLAYER:` *"I had other matters."*
`SERAPHINE:` *"I noticed."*

She says nothing further. Neither does the player.

+2 Affection — the understated acknowledgment that there is now an expectation.

---

### STAGE 6 — "The Entanglement" (Affection 73–82, Days 59–70)

*She is fully compromised and she knows it. The question now is what she will do about it.*
*New visits unlock: "Private Study" (Route B/C, full adult scene, 2 day cooldown), "Morning Walk" (Route A, romantic scene, adult-possible, 2 day cooldown).*

**Scene 6-A (Devotion ≥ 48, Day 60+) — "Her Secret"**

`SERAPHINE:` *"I was in the room when he signed the order. I was his court scholar. I transcribed it."*
`PLAYER:` *"And you said nothing."*
`SERAPHINE:` *"I was twenty-three years old and afraid for my life. I have carried it since."*

- `[A]` *"It was not yours to fix alone."* → +8 Dev (she takes his/her hand. Does not let go immediately.)
- `[B]` *"Fear is reasonable. What matters is what you do with it now."* → +5 Dev
- `[C]` *"You have the document."* → +4 Dom (*"...Yes."* Cold and accurate. She meets his/her eyes.)

+10 Affection, flag `yvara_knows_truth`, unlocks Governor subplot

**Scene 6-B (Dominion ≥ 48, Day 60+) — "The Agreement"**

She raises it herself. She wants to name what has happened before it names itself.

`SERAPHINE:` *"I find I cannot account for... this. Whatever this has become."*
`PLAYER:` *"Then stop trying to account for it."*
`SERAPHINE:` *"That is not how I am built."*
`PLAYER:` *"I know. That is half the point."*

- `[A]` *"Then let me account for it. Stay — not as a patron's arrangement."* → pivots toward Combined Route
- `[B]` *"The accounting is simple. You are here because you want to be."* → +8 Dom (*"...Yes."*)

+10 Affection, major branch point

**Scene 6-C (Affection 68+, Day 64+) — "The Inquisitor"**

A Governor agent visits the Academy. Yvara handles him — she is practiced — but afterward she is shaken. The player was present.

Three route variants:

- Route A: He/she puts a hand on her shoulder. She covers it with hers.
- Route B: *"He will not come back."* She does not ask how he/she can be certain. She simply believes it.
- Route C: `SERAPHINE:` *"I am beginning to understand why people choose to trust someone terrible."* `PLAYER:` *"I am not terrible."* `SERAPHINE:` *"No. That is the trouble."*

+5 Affection, Governor tension rises, agent now knows she is here

---

### ADULT EVENT 2 — Route-Specific Full Scene (Stage 6, NSFW, Days 62–70)

Each route gets a dedicated adult scene in Stage 6, separate from the endings.

**Route A — "The Study"** *(Devotion ≥ 55, Day 62+)*

She invites him/her to the back library — the part students never see, where her personal collection lives. There is wine. She did not tell him/her she was going to do this. She is not entirely sure why she did.

The scene is unhurried. There is talking, and then less talking. She closes the distance again, but this time she does not pull back.
→ *[Full NSFW romantic scene: tender, she chooses every part of it.]*

**Route B — "The Command"** *(Dominion ≥ 55, Day 62+, unlocked via "Private Study" visit)*

The "Private Study" visits have been sharpening the dynamic for days. This time the player does not stop at the usual point.

`SERAPHINE:` *"You will not make me ask."*
`PLAYER:` *"No. I will not."*

She does not ask. She does something better.
→ *[Full NSFW explicit scene: domination dynamic, she participates fully and actively.]*

**Route C — "The Decision"** *(Both ≥ 42, Day 62+)*

`SERAPHINE:` *"You have been running both at once. The gentle approach and the other one. I want to know which one is real."*
`PLAYER:` *"Both."*
`SERAPHINE:` *"...That is either the most honest or the most troubling answer I have ever received."*

She decides to take him/her at his/her word.
→ *[Full NSFW combined scene: begins on equal footing, shifts as the scene progresses.]*

---

### STAGE 7 — "The Threshold" (Affection 83–90, Days 71–82)

*The route-specific scenes have fired. What remains is the thing each route arrives at when there is nothing left to approach cautiously.*

---

### ADULT EVENT 3 — "The Threshold" (Stage 7, NSFW, Routes B/C only)

**Unlock condition:** Enchanted Amulet must have been gifted to Yvara at Stage 3+, Route-specific adult scene (Stage 6) must have fired, Affection ≥ 83, Day 72+.

This scene cannot be triggered — it fires automatically on the next visit after conditions are met. It is the only scene in the arc that requires a specific item to unlock.

---

The player arrives. She is at her desk. The amulet is on the surface in front of her — she has been looking at it. She did not expect him/her today.

`SERAPHINE:` *"I have been... considering the appropriate response to this."*

The player says nothing. Waits.

`SERAPHINE:` *(a slow exhale)* *"I believe the appropriate response is this."*

She stands. She moves to the center of the room — away from her desk, away from the books, away from everything that makes her a scholar and a proprietor. She puts the amulet on. Then she kneels.

Not dramatically. Not like someone breaking. Like someone who has made a specific, considered decision and is executing it with full competence.

`PLAYER:` *"You did not have to—"*
`SERAPHINE:` *"I am aware."*

A pause.

`SERAPHINE:` *"That is rather the point."*

**Route B version:**
→ *[Full NSFW, explicit — position play, consensual restraint, the most physically intense scene in the B route. The distinctive element: she is not passive within this. She is directing the player toward precisely what she wants, from within the dynamic she has accepted. Her submission is specific, articulate, and entirely intentional. The scene is "hardcore" in the sense that nothing is left implicit.]*

**Route C version:**
She kneels — but she looks up and reaches for his/her hand and pulls him/her down beside her.

`SERAPHINE:` *"If this is what we are, then we are both in it."*

→ *[Full NSFW, explicit — mutual dynamic. Incorporates physical restraint elements but neither participant is purely dominant or purely yielding. The scene is more intense than "The Decision" in Stage 5 — less exploratory, more certain.]*

After this scene: a new flag `threshold_crossed` is set. The Stage 8 ending scenes reference this moment — her dialogue in the ending is different if it has fired.

---

### ADULT EVENT 4 — "The Night She Stayed" (Stage 7, NSFW, Route A only)

**Unlock condition:** Route A dominant (Devotion ≥ 65, Dominion < 30), "The Study" scene (Stage 6) must have fired, Affection ≥ 83, Day 72+.

Route A has no equivalent to The Threshold — a scene that is explicitly chosen, deliberate, and final in what it says about the relationship. This is it.

The player does not leave after the evening. She does not ask him/her to. In the morning, for the first time, she does not pretend the distance was always there.

`SERAPHINE:` *"I have been thinking."*
`PLAYER:` *"About?"*
`SERAPHINE:` *"Whether I am the kind of person who does this."*

A pause.

`SERAPHINE:` *"I believe I am."*

→ *[Full NSFW romantic scene: the most complete Route A adult scene. More intimate than The Study — quieter, more certain. The scene is less about desire than about the decision to stop pretending the desire is not there. Nothing is left ambiguous.]*

This scene sets flag `night_stayed`. The Stage 8 ending dialogue is altered if this fired — she references the morning, not the first kiss, as the moment she knew.

**New CG: `cg_night_stayed`** — she has turned toward the player. Dawn light through the office window. The image is tender and explicit. One of the two most important Route A images alongside `cg_ending_a`.

---

### STAGE 8 — "Irrevocable" (Affection 91–100, Days 83+)

---

**Scene 8-A — Route A: "Partnership"** *(Devotion ≥ 60, Dominion < 30)*

She has thought about it carefully and reached a conclusion with the rigor she applies to everything.

`SERAPHINE:` *"I wish to propose a modification to our arrangement."*
`PLAYER:` *"I am listening."*
`SERAPHINE:` *"I would like it to be less of an arrangement."*

Beat.

`PLAYER:` *"I can accommodate that."*

She gives him/her the document. Not as leverage — as a gift.
→ *[NSFW romantic scene: she initiates with certainty. The best version of the Route A adult scenes.]*

**Gameplay reward:** Governor document. Yvara stays independent — does not become a worker. Permanent advisor NPC: daily +Reputation bonus, her name in the UI. "Private Arrangement" repeatable visit unlocked.

---

**Scene 8-B — Route B: "Surrender"** *(Dominion ≥ 60, Devotion < 30)* [Full NSFW]

She chose this, slowly, one small capitulation at a time. She is not broken. That is exactly what makes it work.

`SERAPHINE:` *"I find I no longer know how to be anything else."*
`PLAYER:` *"You do not have to be."*
`SERAPHINE:` *"...No. I suppose I do not."*

She hands over the document. She hands over more than that.
→ *[Full NSFW explicit scene: clearest expression of the domination dynamic.]*

**Gameplay reward:** Governor document. Yvara remains as a permanent non-worker NPC. The Academy gains a passive daily +Reputation bonus from her presence, labeled in the UI as her contribution. "Private Arrangement" repeatable visit unlocked.

---

**Scene 8-C — Route C: "Balance"** *(Both ≥ 40)* [Best Ending, NSFW]

`SERAPHINE:` *"You are a contradiction."*
`PLAYER:` *"How so?"*
`SERAPHINE:` *"Hard enough to break things. Deliberate enough to choose not to."*
`PLAYER:` *"And you?"*
`SERAPHINE:` *"I am beginning to suspect I would let you. Which is its own kind of contradiction."*

→ *[Full NSFW combined scene: begins tender, she shifts it mid-scene. She initiates the change herself.]*

**Gameplay reward:** Governor document. Yvara remains a permanent non-worker NPC. Combined bonus: the Academy generates both +Reputation and +Clever passive bonuses to enrolled workers. "Private Arrangement" repeatable unlocked.

---

## Adult Content Map (Complete)

- **14 adult moments across 8 stages**, behind the existing NSFW toggle
- All three routes now have equivalent depth: **5 full explicit scenes each**, plus 1 non-explicit opener and 1 repeatable
- Route A was previously lighter than B/C — "The Second Visit" (Stage 5) and "The Night She Stayed" (Stage 7) correct that balance


| #   | Stage       | Name                               | Content                                                                    | Route   |
| --- | ----------- | ---------------------------------- | -------------------------------------------------------------------------- | ------- |
| 1   | 3           | "After the Tour"                   | First contact, non-explicit. One CG.                                       | All     |
| 2   | 4           | "The Storm"                        | First full adult scene. One CG.                                            | All     |
| 3   | 4+          | "Evening at Academy" (repeatable)  | Short adult scene, upgrades post-Storm                                     | All     |
| 4   | **5**       | **"The Second Visit"**             | **Full adult scene — first conscious choice after The Storm. One new CG.** | **All** |
| 5   | 6           | "The Study"                        | Full romantic scene                                                        | A       |
| 6   | 6           | "The Command"                      | Full explicit domination scene                                             | B       |
| 7   | 6           | "The Decision"                     | Full combined scene                                                        | C       |
| 8   | 7           | "The Threshold"                    | Hardcore — submission ritual, restraint, position play. Requires Amulet.   | B/C     |
| 9   | **7**       | **"The Night She Stayed"**         | **Full romantic scene, most explicit Route A image. One new CG.**          | **A**   |
| 10  | 8           | Ending 8-A "Partnership"           | Full romantic scene                                                        | A       |
| 11  | 8           | Ending 8-B "Surrender"             | Full explicit scene (altered if Threshold fired)                           | B       |
| 12  | 8           | Ending 8-C "Balance"               | Full combined scene (altered if Threshold fired)                           | C       |
| 13  | Post-ending | "Private Arrangement" (repeatable) | Full adult scene, route-flavored                                           | All     |


---

## Governor Plot Integration

At Stage 5 (`yvara_knows_truth` flag):

- Governor Tension increases as if an objective completed
- Scene 6-C "The Inquisitor" fires — his agent now knows she is here
- Follow-up event: *"The Second Inquisitor"* — Governor escalates. Player spends 800g (clean), sacrifices Reputation (risky), or refuses and risks escalation (bad ending available if Affection < 75)

---

## Estimated Playtime


| Content                                                | Est. Time                     |
| ------------------------------------------------------ | ----------------------------- |
| ~42 scripted scenes × ~3 min avg                       | ~126 min                      |
| Visit interactions across 8 stages (~45 visits played) | ~28 min                       |
| 13 adult scenes/events × ~3–4 min avg                  | ~46 min                       |
| Academy random events (4 events)                       | ~12 min                       |
| **Total**                                              | ~~**212 min (~~3 hr 30 min)** |


---

## Technical Notes

### Background Blur When Yvara Appears

When Yvara's bust is displayed, the background is blurred to push it into the background visually and focus attention on the character — a standard VN technique.

Ren'Py 7.4+ supports a `blur` ATL property applied as a `Transform`. Implementation in `yvara_arc.rpy`:

```renpy
transform yvara_bg:
    blur 3.0
```

Usage in any Yvara scene:

```renpy
show bg_yvara_office at yvara_bg   # background blurred
show yvara_formal neutral              # bust on top, unblurred
```

When Yvara leaves the scene:

```renpy
hide yvara_formal
show bg_yvara_office                   # no transform — blur removed
```

**Blur radius guidance:**

- `blur 2.0` — subtle, background still readable. Good for early-stage professional scenes.
- `blur 3.0` — moderate. Recommended default for most scenes.
- `blur 5.0` — strong. Reserve for emotionally intense or adult scenes.

The radius can be varied by scene to reinforce emotional tone — sharper background for tense/professional moments, heavier blur for intimate ones.

**Performance note:** Ren'Py's built-in `blur` runs on the GPU via GLSL and is lightweight on modern hardware. If performance on older machines is a concern, the fallback is to pre-render one blurred variant per background (adds 3 files to the asset list: `bg_yvara_office_blur`, `bg_yvara_garden_blur`, `bg_yvara_library_blur`) and swap to those instead of using the runtime transform.

---

## Files to Create / Modify

- `[game/data/workers/workers_sfw_unique.json](game/data/workers/workers_sfw_unique.json)` — Add Yvara as NPC (`is_npc: true`, no profession assignment, 6 affection stage thresholds)
- `[game/data/interactions/yvara_visits.json](game/data/interactions/yvara_visits.json)` — All 10 visit options with stage gates, cooldowns, visit-to-scene conversion flags
- `[game/data/events/events_academy.json](game/data/events/events_academy.json)` — 4 Academy random events + The Inquisitor + The Second Visit
- `[game/data/items/items.json](game/data/items/items.json)` — Add Rare Book (~~600g), Fine Wine (~~300g, also event drop)
- `[game/scripts/events/yvara_arc.rpy](game/scripts/events/yvara_arc.rpy)` — All scene labels in archaic English, all adult events, 3 endings. Defines `yvara_prologue` label (called on building purchase) and `yvara_visit` label (called from map Visit button)
- `[game/scripts/buildings/building_logic.rpyc](game/scripts/buildings/building_logic.rpyc)` — Add hook to call `yvara_prologue` after Academy purchase confirmation
- `[game/data/buildings/buildings.json](game/data/buildings/buildings.json)` — Add Academy building type with enrollment fee mechanic and worker Clever/Charm training passive

---

## Off-Camera Relationship Mechanics

Two repeatable mechanics that fill the gaps between story scenes and give the player active things to do during cooldown days. Both are text-only — no new CGs required.

---

### Mechanic A — "The Good Word" (Devotion path, Stage 2+)

The player selects a worker with Romance ≥ 50 and sends them to the Academy for a day under the pretext of extra tutoring. While there, the worker naturally talks about their manager — how they are treated, what the household is like. Yvara, who has spent years hearing workers complain about their employers, finds herself listening differently.

**Mechanic:**

- Accessible from the Academy visit screen: "Send a worker for the day"
- Requires: One worker with Romance ≥ 50, Stage 2+ reached
- Cost: That worker does not generate income that day (assigned to Academy instead)
- Cooldown: 3 days per worker sent; the same worker cannot be sent twice
- Effect: +3 Devotion, +1 Affection

**Narrative escalation:**

- First use: Next visit, she mentions it in passing. Professionally. `SERAPHINE:` *"Your worker spoke of you. Favourably."* She moves on immediately.
- Third use: She is writing something when the player arrives. She pauses. *"They all say the same things. I find that... notable."* `flustered` expression, brief.
- Fifth use (flag `good_word_peak`): She sought out a second worker on her own initiative to ask questions. She does not tell the player this. But the player's workers mention it.

`good_word_peak` gives +5 Devotion when it fires and unlocks a short optional scene on the next visit where she does not quite explain herself.

---

### Mechanic B — "The Observed Lesson" (Dominion path, Stage 3+)

The player complains that a worker is rebellious and asks Yvara, as an educator, to observe one of the household's discipline sessions — purely professionally, to advise on technique. She agrees. It is within her scope. The fee is 200g per session.

She sits at the back of the room and takes notes. She is watching what the player does with someone who has been trained into compliance.

**Mechanic:**

- Accessible from the Academy visit screen: "Request a consultation"
- Requires: Stage 3+ reached, Dom ≥ 14, player has completed at least 2 discipline interactions with any worker
- Cost: 200g per session
- Cooldown: 4 days
- Effect: +4 Dominion per session; accumulates `observed_sessions` counter (max 6)

**Narrative escalation by counter:**

- 1 session: She submits written notes afterward. The language is clinical and precise and exactly the language the player uses during discipline.
- 3 sessions: On the next visit she corrects a student in the corridor with the same phrasing. She freezes when she realizes. Says nothing.
- 5 sessions: During a normal visit exchange she starts to say *"Yes, my—"* and stops. Completes the sentence differently. Her expression: `surprised`, suppressed immediately.
- 6 sessions (flag `lesson_absorbed`): She tells the player the consultations are no longer necessary. When asked why: *"I believe I have absorbed sufficient... methodology."* `knowing` expression. The pause before "methodology" is long.

`lesson_absorbed` gives +6 Dominion when it fires and directly advances the dialogue variant of Scene 5-B "The Agreement" — she uses the absorbed language when she finally names what has happened between them.

---

## Asset Plan

Yvara's assets live in `game/images/yvara/`, following the existing per-character folder convention.

---

### 1. Character Bust

Two outfit variants. **Formal** (Stages 1–2): robes fastened, hair pinned, spectacles on. **Relaxed** (Stage 3+): hair partially down, robes looser, spectacles in hand. The Enchanted Amulet becomes visible in the relaxed variant once given as a gift.

Using the layered approach standard in Ren'Py — one body image per outfit, face overlays applied on top — the draw count stays low while allowing clean transitions between expressions.

**6 expressions, shared across both outfits:**


| Expression  | Description                                      | Used in                                                  |
| ----------- | ------------------------------------------------ | -------------------------------------------------------- |
| `neutral`   | Composed. Default.                               | All Stage 1–2 visits, professional exchanges             |
| `amused`    | The almost-smile. One corner only.               | Cat scene, dry wit, gift reactions Stage 1–2             |
| `surprised` | Caught off guard. Immediately suppressed.        | Unguarded Moment, Good Word third use, *"Yes, my—"* slip |
| `warm`      | Genuine but still guarded. The armor is thinner. | Late Hour, Garden, Gift reactions Stage 3+               |
| `flustered` | The armor cracked. She knows it.                 | Good Word peak, Storm aftermath Route A, Morning After   |
| `yielding`  | Not broken. Resolved. A decision made.           | Favor, Storm Route B, Threshold, Observed Lesson peak    |


**Total: 2 bodies + 6 face overlays = ~14 files → 12 in-game expression combinations**

The `vulnerable` state needed for Her Secret (Scene 5-A) uses the `warm` base with a specific CG rather than a new expression — the CG carries the emotional weight, the bust expression alone doesn't need to.

---

### 2. Backgrounds (3 new, beyond existing game assets)

The game already has Academy exterior assets from the building system. The 3 new backgrounds are specific to Yvara's scenes:


| ID                 | Location                                                                                                                                                               | Used in                                                                 |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| `bg_yvara_office`  | Her office: desk, bookshelves, window. Used for virtually all visits. Two lighting states (day / lamp-lit night) handled as a simple overlay tint, not a second image. | Enrollment, Standards, Ledger, Late Hour, Favor, most Stages 1–4 visits |
| `bg_yvara_garden`  | The Academy garden: bench, overgrown hedges, afternoon light. One image, static.                                                                                       | The Garden (Scene 3-A), Morning Walk visit option                       |
| `bg_yvara_library` | Back library: personal shelves, wine, low light. Only appears Stage 5+.                                                                                                | The Study (Route A adult), private late-stage visits                    |


**3 background images.** Night/storm atmosphere in the office achieved via a darkening overlay and rain audio — no separate asset required.

---

### 3. Scene CGs

Only the scenes that genuinely require an illustration — moments where a full image communicates something the bust + background system cannot.

#### SFW CGs (5)


| ID                 | Scene                              | What it shows                                                                                                   |
| ------------------ | ---------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `cg_cat`           | Scene 1-A — "The Unguarded Moment" | Her back turned, addressing the cat on her papers. Player POV from the doorway. Sets her character immediately. |
| `cg_late_hour`     | Event 2-Y — "The Late Hour"        | Both at a table, books between them, lamp light. The first scene that feels like something other than business. |
| `cg_her_secret`    | Scene 5-A — "Her Secret"           | Her face, fully open. The single most important image in the arc. No armor.                                     |
| `cg_morning_after` | Scene 4-X — "The Morning After"    | Her at the desk. Tea on the edge. The restraint of the moment.                                                  |
| `cg_inquisitor`    | Scene 5-C — "The Inquisitor"       | Both watching the agent leave. The tension of what they have not said.                                          |


#### NSFW CGs (7)

One CG per major adult scene or adult event. Route variants are handled through dialogue, not separate images — except where the visual content is fundamentally different.


| ID                | Scene                                    | What it shows                                                                                                                                          |
| ----------------- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `cg_tour`         | "After the Tour"                         | First real contact. One image — framing is ambiguous enough to work for both routes (his/her hand near her collar; she has not stepped back).          |
| `cg_storm`        | "The Storm"                              | The key moment. One image: she is close, the distance has ended. Route dialogue determines tone; a single well-composed image covers all three routes. |
| `cg_study`        | "The Study" (Route A)                    | Back library, wine. The most intimate Route A image.                                                                                                   |
| `cg_command`      | "The Command" (Route B)                  | The domination dynamic at its clearest before the Threshold.                                                                                           |
| `cg_decision`     | "The Decision" (Route C)                 | Both of them, neither fully leading yet.                                                                                                               |
| `cg_second_visit` | "The Second Visit" (Stage 5, all routes) | The moment before. Route-flavored by dialogue only. One image.                                                                                         |
| `cg_threshold`    | "The Threshold" (Routes B/C)             | She has knelt. The amulet on. One image — the most explicit and most iconic in the arc.                                                                |
| `cg_night_stayed` | "The Night She Stayed" (Route A)         | Dawn light. She has turned toward the player. The most explicit Route A image.                                                                         |
| `cg_ending`       | Endings 8-A / 8-B / 8-C                  | One CG per ending (3 images).                                                                                                                          |


**Total NSFW CGs: 11** (8 entries above, with `cg_ending` being 3 images)

---

### Asset Summary


| Category                                                    | Count        |
| ----------------------------------------------------------- | ------------ |
| Character bust files (2 bodies + 6 face overlays)           | 14 files     |
| SFW scene CGs                                               | 5            |
| NSFW scene CGs                                              | 11           |
| Backgrounds                                                 | 3            |
| UI portrait (small thumbnail, 2 variants: formal / relaxed) | 2            |
| **Total**                                                   | **35 files** |


The bust system is layered — body and face are separate image files composited in Ren'Py at display time.

**Production priority order:**

1. `yvara_formal` body + `neutral` face overlay — needed for Scene 0 (fires on building purchase). Nothing else can be shown without these.
2. `bg_yvara_office` (day) — needed for Scene 0 and all Stage 1–2 visits.
3. Remaining 5 face overlays (`amused`, `surprised`, `warm`, `flustered`, `yielding`) — needed before Stage 2 content.
4. `yvara_relaxed` body — needed from Stage 3 onward.
5. `bg_yvara_garden`, `bg_yvara_library` — needed for Stage 3 and Stage 5+ respectively.
6. SFW CGs in order: `cg_her_secret` → `cg_late_hour` → `cg_inquisitor` → `cg_morning_after` → `cg_cat`
7. NSFW CGs in order: `cg_threshold` → `cg_night_stayed` → `cg_storm` → `cg_second_visit` → three `cg_ending` images → `cg_study` / `cg_command` / `cg_decision` → `cg_tour`

