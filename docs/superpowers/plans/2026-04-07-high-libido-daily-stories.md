# High Libido Daily Stories Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add high-libido variant daily stories (`stat_requirements.libido: 20`) across all professions in all buildings, and change `rest_nsfw` libido drain from -3 to -10.

**Architecture:** All changes are JSON-only in `game/data/buildings/building_types.json`. Each new story is a "libido version" of an existing profession task — same `skill_options` (so the image fallback chain lands on the same skill-based images like `wait`, `service`, `charm`, `combat`, etc.), but with racier narrative, `nsfw_only: true`, `stat_requirements.libido: 20`, higher `difficulty_modifier`, and `-10 libido` drain on success/critical_success.

**Tech Stack:** JSON data file, Ren'Py engine (reads JSON at runtime)

---

## Key Constraints

### Image Fallback Safety
The image system (`event_visuals.rpy:475`) resolves images in this priority:
1. `story_image` match in worker folder (with/without traits)
2. `skill_name` match in worker folder (with/without traits)
3. Same searches in default folder (`blossom`/`guy`)
4. Profile image

**Rule:** Every new story must use `skill_options` that map to existing image patterns. The `story_image` can be a custom name (it will miss, which is fine), but the `skill_options` fallback MUST land on images that exist. For example:
- `"skill_options": ["Charm"]` → fallback searches for `charm_*` images (exist in all workers)
- `"skill_options": ["Charm", "Service"]` → fallback searches for `charm_*` or `wait_*`/`service_*`/`maid_*` images
- `"skill_options": ["Sex"]` → fallback searches for `sex_*` images
- `"skill_options": ["Combat"]` → fallback searches for `combat_*` images

### Story Pattern
Each new story follows this template (from the user's example):
```json
{
  "id": "{profession}_story_libido20",
  "weight": 20,
  "report": "Short Evocative Title",
  "description": "{worker_name} one-liner about what the high-libido situation looks like.",
  "nsfw_only": true,
  "difficulty_modifier": 10,
  "skill_options": ["SameSkillAsBaseStory"],
  "stat_requirements": { "libido": 20 },
  "descriptions": {
    "failure": "...",
    "mediocre": "...",
    "success": "...",
    "critical_success": "..."
  },
  "earnings": { same formula as base story },
  "consequences": {
    "failure": { "energy": -X, "joy": -2, "rebelliousness": 1, "reputation": -10, "libido": -5 },
    "success": { "energy": -X, "joy": 2, "reputation": 10, "libido": -10 },
    "critical_success": { "energy": -X, "joy": 3, "reputation": 15, "libido": -10 }
  },
  "story_image": "{profession}_story_libido20",
  "failure_image": "{profession}_story_libido20_failure"
}
```

**Weight 20** ensures these stories fire frequently when libido is high enough.

### Mechanical Rules (all new libido stories)
- `"stat_requirements": { "libido": 20 }` — only triggers when worker has ≥20 libido
- `"nsfw_only": true` — only appears when NSFW mode is on
- Success/critical_success: `"libido": -10` (the main drain mechanic)
- Failure: `"libido": -5` (partial drain even on failure)
- `"difficulty_modifier": 10` — distraction makes the task harder
- `"weight": 20` — high priority when available

---

## File Structure

- **Modify:** `game/data/buildings/building_types.json`
  - Brothel professions: prostitute (~line 32), masseuse (~line 556), expert_attendant (~line 758), stripper (~line 1541), service (~line 1808)
  - Restaurant professions: service (~line 2009), cook (~line 2212)
  - Adventurer's Guild professions: adventurer (~line 2533)
  - Tavern professions: bartender (~line 3726), entertainer (~line 3900)
  - Casino professions: dealer (~line 4400), guard (~line 4571)
  - Castle professions: ambassador (~line 5067), courtesan (~line 5200+)
  - All `rest_nsfw` entries: brothel (~line 1976), restaurant (~line 2498), adventurers_guild (~line 3692), tavern (~line 4367), casino (~line 5033)

---

## Task 1: Change all rest_nsfw libido drain from -3 to -10

**Files:**
- Modify: `game/data/buildings/building_types.json` — all `rest_nsfw_relief_*` entries

This is the simplest change: find every `rest_nsfw_relief_*` story and change `"libido": -3` to `"libido": -10` in their consequences.

- [ ] **Step 1: Update rest_nsfw_relief_brothel (line ~1976)**

Change:
```json
"libido": -3
```
To:
```json
"libido": -10
```

- [ ] **Step 2: Update rest_nsfw_relief_restaurant (line ~2498)**

Same change: `"libido": -3` → `"libido": -10`

- [ ] **Step 3: Update rest_nsfw_relief_adventurers_guild (line ~3692)**

Same change: `"libido": -3` → `"libido": -10`

- [ ] **Step 4: Update rest_nsfw_relief_tavern (line ~4367)**

Same change: `"libido": -3` → `"libido": -10`

- [ ] **Step 5: Update rest_nsfw_relief_casino (line ~5033)**

Same change: `"libido": -3` → `"libido": -10`

- [ ] **Step 6: Validate JSON**

Run:
```bash
python -c "import json; json.load(open('game/data/buildings/building_types.json', encoding='utf-8')); print('JSON valid')"
```
Expected: `JSON valid`

- [ ] **Step 7: Commit**

```bash
git add game/data/buildings/building_types.json
git commit -m "fix: rest_nsfw libido drain -3 → -10 for all buildings"
```

---

## Task 2: Add high-libido stories to Brothel professions

**Files:**
- Modify: `game/data/buildings/building_types.json` — brothel section

Add one libido story per profession. Each goes at the end of the profession's `daily_stories` array.

- [ ] **Step 1: Add prostitute libido story**

Insert after the last story in the `prostitute` profession's `daily_stories` array (after `prostitute_homo_client_female`, before the `]` closing the array):

```json
{
  "id": "prostitute_libido20_heat",
  "weight": 20,
  "report": "Desperate Heat",
  "description": "{worker_name} is burning up with need and begs the next client to take them hard — no foreplay, no pretence.",
  "nsfw_only": true,
  "difficulty_modifier": 10,
  "skill_options": ["Sex"],
  "stat_requirements": { "libido": 20 },
  "descriptions": {
    "failure": "{worker_name} throws themselves at the client so hungrily that it startles rather than excites. The frantic clawing and breathless begging feel desperate, not seductive — the client pulls away, clothes half-undone, and leaves the room embarrassed for them both.",
    "mediocre": "{worker_name} drags the client to the bed before the door shuts and rides them raw, but the frantic pace leaves no room for finesse. The client finishes quickly and tips the minimum, unsure whether they just had a service or got ambushed.",
    "success": "{worker_name}'s shameless need becomes the show itself. Pinning the client down and taking what they want with rolling hips and breathless commands, the raw hunger drives the client to a shuddering finish. Coin hits the table before the sweat dries.",
    "critical_success": "{worker_name} channels pure lust into an hour of relentless, sweat-soaked sex that leaves the client boneless and stammering gratitude. Word travels fast — three bookings arrive before the day is out, all requesting 'the one who can't get enough.'"
  },
  "earnings": {
    "success": "100 + skill",
    "critical_success": "100 + skill * 2",
    "mediocre": "skill",
    "failure": "-(roll - skill)"
  },
  "consequences": {
    "failure": { "energy": -4, "joy": -2, "rebelliousness": 1, "reputation": -10, "libido": -5 },
    "mediocre": { "energy": -4, "joy": -1, "reputation": -5, "libido": -5 },
    "success": { "energy": -4, "joy": 2, "reputation": 10, "libido": -10 },
    "critical_success": { "energy": -3, "joy": 3, "reputation": 15, "libido": -10 }
  },
  "story_image": "prostitute_libido20",
  "failure_image": "prostitute_libido20_failure",
  "positive_traits": { "Nympho": 5, "High Libido": 4, "Porn Star": 3, "Energetic": 3 },
  "negative_traits": { "Shy": 4, "Conservative": 3 },
  "trait_msg_success": "{worker_name}'s {trait} turns desperation into irresistible hunger.",
  "trait_msg_failure": "{worker_name}'s {trait} couldn't salvage the frantic encounter."
}
```

- [ ] **Step 2: Add masseuse libido story**

Insert at the end of the `masseuse` profession's `daily_stories` array (after `masseuse_hand_oil_edge`):

```json
{
  "id": "masseuse_libido20_oiled_surrender",
  "weight": 20,
  "report": "Oiled Surrender",
  "description": "{worker_name} can barely keep hands professional — the oil, the skin, the closeness push them past restraint.",
  "nsfw_only": true,
  "difficulty_modifier": 10,
  "skill_options": ["Hand"],
  "stat_requirements": { "libido": 20 },
  "descriptions": {
    "failure": "{worker_name}'s hands drift south before the client gives any signal, oil-slick fingers crossing lines that weren't offered. The client stiffens, pulls away, and dresses in silence. A complaint follows before sundown.",
    "mediocre": "{worker_name} can't hide the trembling — fingers press too deep, linger too long in the wrong places. The client notices but plays along, half-flattered. The 'happy ending' is clumsy and rushed, over before the candle gutters.",
    "success": "{worker_name} lets need flow through skilled hands. What starts as a thigh massage becomes slow, deliberate edging — oil-slick fingers teasing until the client arches and begs. The release is explosive, and {worker_name} finally exhales too, tension draining with every stroke.",
    "critical_success": "{worker_name} turns aching want into an art form. Every pass of oiled palms is a confession — hip, inner thigh, the hollow of the throat — until the line between massage and foreplay dissolves. The client comes undone twice, then insists on returning the favour. Both walk out glowing."
  },
  "earnings": {
    "success": "50 + skill",
    "critical_success": "50 + skill * 2",
    "mediocre": "skill",
    "failure": "-(roll - skill)"
  },
  "consequences": {
    "failure": { "energy": -3, "joy": -2, "rebelliousness": 1, "reputation": -8, "libido": -5 },
    "mediocre": { "energy": -3, "joy": -1, "reputation": -3, "libido": -5 },
    "success": { "energy": -3, "joy": 2, "reputation": 8, "libido": -10 },
    "critical_success": { "energy": -2, "joy": 3, "reputation": 12, "libido": -10 }
  },
  "story_image": "masseuse_libido20",
  "failure_image": "masseuse_libido20_failure",
  "positive_traits": { "Nympho": 5, "High Libido": 4, "Delicate": 3, "Playful": 3 },
  "negative_traits": { "Shy": 3, "Conservative": 4 },
  "trait_msg_success": "{worker_name}'s {trait} turns the massage into something neither will forget.",
  "trait_msg_failure": "{worker_name}'s {trait} couldn't mask the desperation."
}
```

- [ ] **Step 3: Add expert_attendant libido story**

Insert at the end of the `expert_attendant` profession's `daily_stories` array (after `ea_prostitute_extreme_client`):

```json
{
  "id": "ea_libido20_unhinged_session",
  "weight": 20,
  "report": "Unhinged Session",
  "description": "{worker_name} is wound so tight with need that the next booking becomes a blur of sweat, noise, and broken furniture.",
  "nsfw_only": true,
  "difficulty_modifier": 10,
  "skill_options": ["Sex", "BDSM", "Special"],
  "stat_requirements": { "libido": 20 },
  "descriptions": {
    "failure": "{worker_name} loses all composure the moment the client touches them — grabbing, biting, tearing clothes. The client panics at the intensity, pushes {worker_name} off, and storms out demanding a refund. The room looks like a battlefield.",
    "mediocre": "{worker_name} throws the client onto the bed and takes charge with feral intensity, but the lack of pacing exhausts both of them too fast. The client finishes in minutes and leaves confused — satisfied physically but unsure what just happened.",
    "success": "{worker_name} channels raw need into a session that pushes every boundary the client asked for and several they didn't know they wanted. Hands, mouth, body — all moving with urgent precision. The client staggers out flushed and wide-eyed, already telling friends about the experience.",
    "critical_success": "{worker_name} turns overwhelming desire into the most intense booking the establishment has ever logged. The session spans hours, cycling through positions and acts with tireless hunger. The client is left shaking, hoarse, and utterly devoted — they tip triple and book a standing weekly appointment."
  },
  "earnings": {
    "success": "100 + skill * 2",
    "critical_success": "100 + skill * 3",
    "mediocre": "skill",
    "failure": "-(roll - skill)"
  },
  "consequences": {
    "failure": { "energy": -5, "health": -1, "joy": -3, "rebelliousness": 2, "reputation": -12, "libido": -5 },
    "mediocre": { "energy": -5, "joy": -1, "reputation": -5, "libido": -5 },
    "success": { "energy": -5, "joy": 2, "reputation": 12, "libido": -10 },
    "critical_success": { "energy": -4, "joy": 3, "reputation": 20, "libido": -10 }
  },
  "story_image": "ea_libido20",
  "failure_image": "ea_libido20_failure",
  "positive_traits": { "Nympho": 5, "High Libido": 4, "Porn Star": 4, "Energetic": 3 },
  "negative_traits": { "Shy": 4, "Meek": 3 },
  "trait_msg_success": "{worker_name}'s {trait} turns raw hunger into a legendary session.",
  "trait_msg_failure": "{worker_name}'s {trait} couldn't contain the frenzy."
}
```

- [ ] **Step 4: Add stripper libido story**

Insert at the end of the `stripper` profession's `daily_stories` array (after `stripper_lapdance_escalation`):

```json
{
  "id": "stripper_libido20_stage_fever",
  "weight": 20,
  "report": "Stage Fever",
  "description": "{worker_name} is so aroused the stage act turns from tease into something far more explicit than planned.",
  "nsfw_only": true,
  "difficulty_modifier": 10,
  "skill_options": ["Striptease"],
  "stat_requirements": { "libido": 20 },
  "descriptions": {
    "failure": "{worker_name} can't hold back on stage — touching themselves openly, grinding the pole with unmistakable intent. The audience shifts from titillated to uncomfortable. A few leave. Management pulls {worker_name} off mid-act.",
    "mediocre": "{worker_name}'s routine crosses from seductive to obscene — fingers lingering, moans escaping, hips rolling with genuine urgency. The crowd isn't sure whether to cheer or look away. Tips are average; some patrons mutter about boundaries.",
    "success": "{worker_name} rides the edge between art and indecency like a tightrope. Each reveal is breathless and real — flushed skin, trembling thighs, barely-stifled gasps — and the audience is riveted. The act ends with {worker_name} on their knees, chest heaving, and gold raining onto the stage.",
    "critical_success": "{worker_name} turns aching need into the most electrifying show the tavern has ever seen. Every movement screams genuine desire — the kind no performer can fake — and the entire room holds its breath. When the final piece of cloth falls, the silence breaks into a roar. The tip jar overflows and three VIPs fight to book private time."
  },
  "earnings": {
    "success": "50 + skill * 2",
    "critical_success": "50 + skill * 3",
    "mediocre": "skill",
    "failure": "-(roll - skill)"
  },
  "consequences": {
    "failure": { "energy": -4, "joy": -2, "rebelliousness": 1, "reputation": -10, "libido": -5 },
    "mediocre": { "energy": -4, "joy": -1, "reputation": -3, "libido": -5 },
    "success": { "energy": -4, "joy": 2, "reputation": 10, "libido": -10 },
    "critical_success": { "energy": -3, "joy": 3, "reputation": 18, "libido": -10 }
  },
  "story_image": "stripper_libido20",
  "failure_image": "stripper_libido20_failure",
  "positive_traits": { "Nympho": 5, "High Libido": 4, "Sexy Air": 4, "Graceful": 3 },
  "negative_traits": { "Shy": 5, "Conservative": 4 },
  "trait_msg_success": "{worker_name}'s {trait} turns desperate need into magnetic stage presence.",
  "trait_msg_failure": "{worker_name}'s {trait} couldn't disguise how out of control things got."
}
```

- [ ] **Step 5: Add brothel service libido story**

Insert at the end of the brothel `service` profession's `daily_stories` array (after `service_story1`):

```json
{
  "id": "service_libido20_distracted_shift",
  "weight": 20,
  "report": "Distracted Shift",
  "description": "{worker_name} can barely focus on pouring drinks — every patron's glance feels like an invitation.",
  "nsfw_only": true,
  "difficulty_modifier": 10,
  "skill_options": ["Charm"],
  "stat_requirements": { "libido": 20 },
  "descriptions": {
    "failure": "{worker_name} drops a tray trying to flirt with three tables at once. The flushed cheeks and wandering eyes read as unprofessional, not charming. Regulars raise eyebrows and the shift ends in a lecture from management.",
    "mediocre": "{worker_name} flirts more than serves — lingering touches when handing mugs, bending low more often than necessary. Some patrons enjoy the attention; others just want their food. Tips are uneven and the kitchen complains about slow orders.",
    "success": "{worker_name} channels restless energy into magnetic hospitality. Leaning close to hear orders, brushing hands when serving, eyes that promise without words. Patrons linger longer, order more, and tip generously for the electric atmosphere.",
    "critical_success": "{worker_name} turns smouldering need into the most intoxicating service shift the establishment has ever seen. Every interaction crackles with tension — a whispered recommendation, a stolen glance, a touch that lingers one heartbeat too long. The room buzzes, tabs run high, and a queue forms at the door."
  },
  "earnings": {
    "success": "50 + skill",
    "critical_success": "50 + skill * 2",
    "mediocre": "skill",
    "failure": "-(roll - skill)"
  },
  "consequences": {
    "failure": { "energy": -3, "joy": -2, "rebelliousness": 1, "reputation": -8, "libido": -5 },
    "mediocre": { "energy": -3, "joy": -1, "reputation": -3, "libido": -5 },
    "success": { "energy": -3, "joy": 2, "reputation": 8, "libido": -10 },
    "critical_success": { "energy": -2, "joy": 3, "reputation": 12, "libido": -10 }
  },
  "story_image": "service_libido20",
  "failure_image": "service_libido20_failure",
  "positive_traits": { "Nympho": 4, "High Libido": 3, "Charming": 3, "Sexy Air": 3 },
  "negative_traits": { "Shy": 3, "Conservative": 3 },
  "trait_msg_success": "{worker_name}'s {trait} makes the restless energy irresistible to patrons.",
  "trait_msg_failure": "{worker_name}'s {trait} couldn't hide how distracted they were."
}
```

- [ ] **Step 6: Validate JSON**

```bash
python -c "import json; json.load(open('game/data/buildings/building_types.json', encoding='utf-8')); print('JSON valid')"
```

- [ ] **Step 7: Commit**

```bash
git add game/data/buildings/building_types.json
git commit -m "feat: add high-libido daily stories to all brothel professions"
```

---

## Task 3: Add high-libido stories to Restaurant professions

**Files:**
- Modify: `game/data/buildings/building_types.json` — restaurant section

- [ ] **Step 1: Add restaurant service libido story**

Insert at the end of the restaurant `service` profession's `daily_stories` array (after `service_generous_tipper_nsfw_restaurant`):

```json
{
  "id": "service_libido20_flirty_floor",
  "weight": 20,
  "report": "Flirty Floor Shift",
  "description": "{worker_name} can't stop sizing up every patron who walks through the door — the serving suffers, but the charm doesn't.",
  "nsfw_only": true,
  "difficulty_modifier": 10,
  "skill_options": ["Charm"],
  "stat_requirements": { "libido": 20 },
  "descriptions": {
    "failure": "{worker_name} openly flirts with a table of merchants, ignoring the rest of the dining room. Orders pile up, food goes cold, and a noble couple storms out when their wine is served to the wrong table. The head chef throws a ladle.",
    "mediocre": "{worker_name} floats between tables in a haze of heat, dropping compliments and lingering glances along with the courses. Service is slow but nobody complains — the distraction is too charming to resent. Tips are middling.",
    "success": "{worker_name} turns restless energy into electric hospitality. Every table feels personally attended — a whispered wine recommendation here, a lingering brush of fingers there. Diners stay longer, order dessert they didn't plan on, and leave smiling.",
    "critical_success": "{worker_name} makes the entire restaurant feel like a private affair. The flush in their cheeks and sparkle in their eyes convince every patron they're the only one in the room. Reservations double for the week, and a merchant house asks about hosting private dinners."
  },
  "earnings": {
    "success": "50 + skill",
    "critical_success": "50 + skill * 2",
    "mediocre": "skill",
    "failure": "-(roll - skill)"
  },
  "consequences": {
    "failure": { "energy": -3, "joy": -2, "rebelliousness": 1, "reputation": -8, "libido": -5 },
    "mediocre": { "energy": -3, "joy": -1, "reputation": -3, "libido": -5 },
    "success": { "energy": -3, "joy": 2, "reputation": 8, "libido": -10 },
    "critical_success": { "energy": -2, "joy": 3, "reputation": 14, "libido": -10 }
  },
  "story_image": "service_libido20_restaurant",
  "failure_image": "service_libido20_restaurant_failure",
  "positive_traits": { "Nympho": 4, "High Libido": 3, "Charming": 4, "Beautiful": 3 },
  "negative_traits": { "Shy": 3, "Clumsy": 3 },
  "trait_msg_success": "{worker_name}'s {trait} turns heated distraction into captivating hospitality.",
  "trait_msg_failure": "{worker_name}'s {trait} made the distraction worse."
}
```

- [ ] **Step 2: Add cook libido story**

Insert at the end of the `cook` profession's `daily_stories` array (after `cook_fire_crisis_restaurant`):

```json
{
  "id": "cook_libido20_kitchen_steam",
  "weight": 20,
  "report": "Kitchen Steam",
  "description": "{worker_name} can't keep their mind on the stove — the heat in the kitchen matches the heat under their skin.",
  "nsfw_only": true,
  "difficulty_modifier": 10,
  "skill_options": ["Service"],
  "stat_requirements": { "libido": 20 },
  "descriptions": {
    "failure": "{worker_name} burns two courses staring at the server who keeps bending to clear low tables. The sauce breaks, the roast chars, and the kitchen fills with smoke and swearing. Plates go out late and wrong.",
    "mediocre": "{worker_name} cooks on autopilot, mind somewhere else entirely. The food is edible but uninspired — a step below the restaurant's standard. The head server notices the glazed look but says nothing.",
    "success": "{worker_name} pours frustrated energy into the food itself. Every dish arrives aggressive with flavour — heavier spice, richer sauces, bolder presentation. Diners notice the intensity and clean their plates without a word left to say.",
    "critical_success": "{worker_name} cooks like someone possessed. The pent-up tension translates into dishes that border on obscene in their richness — buttery, indulgent, sinfully good. The dining room falls quiet with pleasure. A food critic in the corner scribbles furiously."
  },
  "earnings": {
    "success": "50 + skill",
    "critical_success": "50 + skill * 2",
    "mediocre": "skill",
    "failure": "-(roll - skill)"
  },
  "consequences": {
    "failure": { "energy": -4, "joy": -2, "rebelliousness": 1, "reputation": -8, "libido": -5 },
    "mediocre": { "energy": -4, "joy": -1, "reputation": -3, "libido": -5 },
    "success": { "energy": -4, "joy": 2, "reputation": 8, "libido": -10 },
    "critical_success": { "energy": -3, "joy": 3, "reputation": 14, "libido": -10 }
  },
  "story_image": "cook_libido20",
  "failure_image": "cook_libido20_failure",
  "positive_traits": { "Nympho": 4, "High Libido": 3, "Clever": 3, "Hardworking": 3 },
  "negative_traits": { "Lazy": 3, "Nervous": 3 },
  "trait_msg_success": "{worker_name}'s {trait} channels frustration into unforgettable cooking.",
  "trait_msg_failure": "{worker_name}'s {trait} made the kitchen chaos worse."
}
```

- [ ] **Step 3: Validate JSON and commit**

```bash
python -c "import json; json.load(open('game/data/buildings/building_types.json', encoding='utf-8')); print('JSON valid')"
git add game/data/buildings/building_types.json
git commit -m "feat: add high-libido daily stories to restaurant professions"
```

---

## Task 4: Add high-libido stories to Adventurer's Guild

**Files:**
- Modify: `game/data/buildings/building_types.json` — adventurers_guild section

- [ ] **Step 1: Add adventurer libido story**

Insert at the end of the `adventurer` profession's `daily_stories` array. Note: adventurer has multiple stories with different skill_options (`Combat`, `Agility`, `Clever`, `Craft`). The libido story should use `Combat` and `Agility` as these are the most common combat skills with existing images.

```json
{
  "id": "adventurer_libido20_reckless_hunt",
  "weight": 20,
  "report": "Reckless Hunt",
  "description": "{worker_name} charges into the wilderness looking for anything — monster, bandit, brawl — to burn off the ache.",
  "nsfw_only": true,
  "difficulty_modifier": 10,
  "skill_options": ["Combat", "Agility"],
  "stat_requirements": { "libido": 20 },
  "descriptions": {
    "failure": "{worker_name} fights with reckless abandon, throwing themselves at every threat without regard for safety. The distraction proves nearly fatal — a wolf pack exploit the careless openings and {worker_name} barely escapes, bloodied, bruised, and still burning.",
    "mediocre": "{worker_name} hacks through undergrowth and lesser beasts in a frustrated blur. The hunt is sloppy — overkill on a boar, a missed trap, wrong turns. The bounty is small and the pent-up energy barely dented.",
    "success": "{worker_name} turns restless aggression into terrifying efficiency. Every swing lands harder than it needs to, every sprint covers ground faster than expected. The monster drops fast and the long walk back finally cools the blood. A decent bounty and aching muscles — both welcome.",
    "critical_success": "{worker_name} fights like something feral let off its chain. The target never stood a chance — {worker_name} is faster, meaner, and utterly relentless. The kill is clean, the loot is rich, and by the time they drag the carcass home, the heat has burned down to a manageable ember. The guild posts the hunt on the legends board."
  },
  "earnings": {
    "success": "50 + skill * 2",
    "critical_success": "50 + skill * 3",
    "mediocre": "skill",
    "failure": "-(roll - skill)"
  },
  "consequences": {
    "failure": { "energy": -5, "health": -5, "joy": -2, "rebelliousness": 1, "reputation": -8, "libido": -5 },
    "mediocre": { "energy": -5, "health": -3, "joy": -1, "reputation": -3, "libido": -5 },
    "success": { "energy": -5, "health": -2, "joy": 2, "reputation": 8, "libido": -10 },
    "critical_success": { "energy": -4, "health": -1, "joy": 3, "reputation": 15, "libido": -10 }
  },
  "story_image": "adventurer_libido20",
  "failure_image": "adventurer_libido20_failure",
  "positive_traits": { "Nympho": 4, "High Libido": 3, "Aggressive": 4, "Energetic": 3 },
  "negative_traits": { "Meek": 3, "Delicate": 3 },
  "trait_msg_success": "{worker_name}'s {trait} turns frustration into a legendary hunt.",
  "trait_msg_failure": "{worker_name}'s {trait} made the reckless charge even more dangerous."
}
```

- [ ] **Step 2: Validate JSON and commit**

```bash
python -c "import json; json.load(open('game/data/buildings/building_types.json', encoding='utf-8')); print('JSON valid')"
git add game/data/buildings/building_types.json
git commit -m "feat: add high-libido daily story to adventurer's guild"
```

---

## Task 5: Add high-libido stories to Tavern professions

**Files:**
- Modify: `game/data/buildings/building_types.json` — tavern section

- [ ] **Step 1: Add bartender libido story**

Insert at the end of the `bartender` profession's `daily_stories` array (after `bartender_last_call_nsfw_tavern`):

```json
{
  "id": "bartender_libido20_uninhibited_shift",
  "weight": 20,
  "report": "Uninhibited Bar Shift",
  "description": "{worker_name} is so worked up they openly flirt and escalate with patrons right on the tavern floor.",
  "nsfw_only": true,
  "difficulty_modifier": 10,
  "skill_options": ["Charm", "Service"],
  "stat_requirements": { "libido": 20 },
  "descriptions": {
    "failure": "{worker_name}'s lack of restraint causes disruptions at the bar. Drinks slosh, orders vanish, and the heated flirting that was meant to charm a table of soldiers instead starts a jealous argument. Management steps in before fists fly.",
    "mediocre": "{worker_name} keeps things mostly functional, but the openly heated behaviour distracts staff and patrons alike. Drinks pour slow, banter veers too personal, and the kitchen sends a runner to ask if the bartender plans to work tonight.",
    "success": "{worker_name}'s bold, uninhibited energy excites the room and drives heavy ordering. Leaning across the bar with flushed cheeks and dangerous smiles, every patron feels like the chosen one. Tabs run long and nobody complains about the wait.",
    "critical_success": "{worker_name} commands the entire bar with shameless confidence, turning the night into a notorious spectacle that packs the tavern. Tips pile up, strangers buy rounds for the house, and by closing time the word on the street is that this is the only tavern worth visiting."
  },
  "earnings": {
    "success": "100 + skill",
    "critical_success": "100 + skill * 2",
    "mediocre": "skill",
    "failure": "-(roll - skill)"
  },
  "consequences": {
    "failure": { "energy": -3, "joy": -2, "rebelliousness": 1, "reputation": -10, "libido": -5 },
    "mediocre": { "energy": -3, "joy": -1, "reputation": -3, "libido": -5 },
    "success": { "energy": -3, "joy": 2, "reputation": 10, "libido": -10 },
    "critical_success": { "energy": -2, "joy": 3, "reputation": 15, "libido": -10 }
  },
  "story_image": "bartender_libido20",
  "failure_image": "bartender_libido20_failure",
  "positive_traits": { "Nympho": 4, "High Libido": 3, "Charming": 4, "Playful": 3 },
  "negative_traits": { "Shy": 4, "Conservative": 3 },
  "trait_msg_success": "{worker_name}'s {trait} turns restless energy into magnetic bar presence.",
  "trait_msg_failure": "{worker_name}'s {trait} couldn't keep the chaos from spilling over."
}
```

- [ ] **Step 2: Add entertainer libido story**

Insert at the end of the `entertainer` profession's `daily_stories` array:

```json
{
  "id": "entertainer_libido20_provocative_show",
  "weight": 20,
  "report": "Provocative Performance",
  "description": "{worker_name}'s act takes a turn — every song, story, and gesture drips with barely-contained want.",
  "nsfw_only": true,
  "difficulty_modifier": 10,
  "skill_options": ["Charm"],
  "stat_requirements": { "libido": 20 },
  "descriptions": {
    "failure": "{worker_name} tries to channel the heat into the performance but it comes across as desperate rather than daring. The ballad turns into an awkward overshare, the dance is more stumble than sway, and patrons shift in their seats. A few walk out.",
    "mediocre": "{worker_name}'s act runs hotter than usual — loaded glances at the audience, lyrics twisted toward innuendo, movements that linger on the edge of scandalous. Some patrons lean in; others order another round to cope. The effect is mixed.",
    "success": "{worker_name} weaves raw desire into every note and gesture. The performance is magnetic — a love song that makes couples grip each other's hands, a dance that stops conversation mid-sentence. The crowd throws coin and demands an encore.",
    "critical_success": "{worker_name} delivers a once-in-a-season performance that the whole district talks about. Every breath, every pause, every stolen glance at the audience crackles with unspoken promise. The tavern falls dead silent, then erupts. Nobles and commoners alike empty their purses, and three bards beg to learn how it's done."
  },
  "earnings": {
    "success": "50 + skill * 2",
    "critical_success": "50 + skill * 3",
    "mediocre": "skill",
    "failure": "-(roll - skill)"
  },
  "consequences": {
    "failure": { "energy": -4, "joy": -2, "rebelliousness": 1, "reputation": -8, "libido": -5 },
    "mediocre": { "energy": -4, "joy": -1, "reputation": -3, "libido": -5 },
    "success": { "energy": -4, "joy": 2, "reputation": 10, "libido": -10 },
    "critical_success": { "energy": -3, "joy": 3, "reputation": 18, "libido": -10 }
  },
  "story_image": "entertainer_libido20",
  "failure_image": "entertainer_libido20_failure",
  "positive_traits": { "Nympho": 4, "High Libido": 3, "Charming": 4, "Sexy Air": 4 },
  "negative_traits": { "Shy": 4, "Nervous": 3 },
  "trait_msg_success": "{worker_name}'s {trait} turns pent-up desire into an unforgettable act.",
  "trait_msg_failure": "{worker_name}'s {trait} made the performance feel more needy than alluring."
}
```

- [ ] **Step 3: Validate JSON and commit**

```bash
python -c "import json; json.load(open('game/data/buildings/building_types.json', encoding='utf-8')); print('JSON valid')"
git add game/data/buildings/building_types.json
git commit -m "feat: add high-libido daily stories to tavern professions"
```

---

## Task 6: Add high-libido stories to Casino professions

**Files:**
- Modify: `game/data/buildings/building_types.json` — casino section

- [ ] **Step 1: Add dealer libido story**

Insert at the end of the `dealer` profession's `daily_stories` array (after `dealer_winners_reward_nsfw_casino`):

```json
{
  "id": "dealer_libido20_heated_table",
  "weight": 20,
  "report": "Heated Table",
  "description": "{worker_name} can barely concentrate on the cards — every brush of fingers during a deal sends a shiver up their spine.",
  "nsfw_only": true,
  "difficulty_modifier": 10,
  "skill_options": ["Service"],
  "stat_requirements": { "libido": 20 },
  "descriptions": {
    "failure": "{worker_name}'s hands shake so badly they misdeal three times in a row. The flirting that was meant to smooth things over lands as awkward desperation. A high-roller accuses them of cheating and security has to escort {worker_name} off the floor.",
    "mediocre": "{worker_name} fumbles through the shift — dealing slow, eyes wandering to every low neckline and tight sleeve at the table. The gamblers notice the distraction and press their advantage. The house edge slips, but not catastrophically.",
    "success": "{worker_name} turns flustered energy into dangerous charm at the table. The heated glances and lingering card passes keep gamblers off-balance and betting recklessly. The house wins big while the players leave feeling they had the time of their lives.",
    "critical_success": "{worker_name} becomes the most magnetic presence on the casino floor. Every deal is a seduction, every smile a dare. High-rollers fight for seats at the table, bet wildly to impress, and lose gleefully. The casino's take is enormous and management considers a permanent raise."
  },
  "earnings": {
    "success": "50 + skill",
    "critical_success": "50 + skill * 2",
    "mediocre": "skill",
    "failure": "-(roll - skill)"
  },
  "consequences": {
    "failure": { "energy": -4, "joy": -2, "rebelliousness": 1, "reputation": -10, "libido": -5 },
    "mediocre": { "energy": -4, "joy": -1, "reputation": -3, "libido": -5 },
    "success": { "energy": -4, "joy": 2, "reputation": 10, "libido": -10 },
    "critical_success": { "energy": -3, "joy": 3, "reputation": 18, "libido": -10 }
  },
  "story_image": "dealer_libido20",
  "failure_image": "dealer_libido20_failure",
  "positive_traits": { "Nympho": 4, "High Libido": 3, "Charming": 4, "Clever": 3 },
  "negative_traits": { "Nervous": 4, "Clumsy": 3 },
  "trait_msg_success": "{worker_name}'s {trait} turns distraction into devastating table charisma.",
  "trait_msg_failure": "{worker_name}'s {trait} made the fumbling worse."
}
```

- [ ] **Step 2: Add guard libido story**

Insert at the end of the `guard` profession's `daily_stories` array:

```json
{
  "id": "guard_libido20_tense_patrol",
  "weight": 20,
  "report": "Tense Patrol",
  "description": "{worker_name} prowls the casino floor coiled tight — every confrontation feels personal, every adrenaline spike doubles.",
  "nsfw_only": true,
  "difficulty_modifier": 10,
  "skill_options": ["Combat"],
  "stat_requirements": { "libido": 20 },
  "descriptions": {
    "failure": "{worker_name} overreacts to a minor dispute between card players, slamming a patron against the wall when a firm word would have sufficed. The casino pays damages and {worker_name} spends the rest of the shift cooling off in the back room, still vibrating with unspent tension.",
    "mediocre": "{worker_name} stalks the floor with visible intensity that makes patrons uneasy. A scuffle at the dice tables is handled competently but with excessive force. The troublemaker is removed, but two bystanders also leave, put off by the aggressive energy.",
    "success": "{worker_name} channels restless energy into an intimidating patrol that keeps every cheat, drunk, and pickpocket on their best behaviour. The coiled tension in {worker_name}'s frame reads as 'don't even think about it.' The floor runs smooth and incident-free.",
    "critical_success": "{worker_name} radiates such controlled menace that the entire casino falls into line without a single confrontation. Even the regulars known for causing trouble order quietly and cash out on time. Management notes the cleanest shift in weeks, and the dealers tip {worker_name} from their own pockets."
  },
  "earnings": {
    "success": "50 + skill",
    "critical_success": "50 + skill * 2",
    "mediocre": "skill",
    "failure": "-(roll - skill)"
  },
  "consequences": {
    "failure": { "energy": -4, "health": -2, "joy": -2, "rebelliousness": 1, "reputation": -10, "libido": -5 },
    "mediocre": { "energy": -4, "health": -1, "joy": -1, "reputation": -3, "libido": -5 },
    "success": { "energy": -4, "joy": 2, "reputation": 8, "libido": -10 },
    "critical_success": { "energy": -3, "joy": 3, "reputation": 15, "libido": -10 }
  },
  "story_image": "guard_libido20",
  "failure_image": "guard_libido20_failure",
  "positive_traits": { "Nympho": 3, "High Libido": 3, "Aggressive": 4, "Strong": 3 },
  "negative_traits": { "Meek": 4, "Nervous": 3 },
  "trait_msg_success": "{worker_name}'s {trait} turns tension into an impenetrable wall of authority.",
  "trait_msg_failure": "{worker_name}'s {trait} made the aggression uncontrollable."
}
```

- [ ] **Step 3: Validate JSON and commit**

```bash
python -c "import json; json.load(open('game/data/buildings/building_types.json', encoding='utf-8')); print('JSON valid')"
git add game/data/buildings/building_types.json
git commit -m "feat: add high-libido daily stories to casino professions"
```

---

## Task 7: Add high-libido stories to Castle professions

**Files:**
- Modify: `game/data/buildings/building_types.json` — governor_castle section

First, check which professions exist in the castle beyond ambassador. The castle has: ambassador, courtesan, spy, and possibly others.

- [ ] **Step 1: Add ambassador libido story**

Insert at the end of the `ambassador` profession's `daily_stories` array:

```json
{
  "id": "ambassador_libido20_charged_diplomacy",
  "weight": 20,
  "report": "Charged Diplomacy",
  "description": "{worker_name} enters negotiations flushed and distracted — every delegate's perfume, every accidental touch under the table, is agony.",
  "nsfw_only": true,
  "difficulty_modifier": 10,
  "skill_options": ["Charm", "Clever"],
  "stat_requirements": { "libido": 20 },
  "descriptions": {
    "failure": "{worker_name} can't focus through the haze of want. Fumbles a key treaty clause while staring at the foreign envoy's collarbone, agrees to unfavourable terms without reading them, and the delegation leaves with the better deal and a knowing smirk.",
    "mediocre": "{worker_name} holds the meeting together by sheer willpower, but the distraction shows in soft concessions and agreements reached too quickly. The deal is done — functional but lopsided. At least nobody noticed the trembling hands.",
    "success": "{worker_name} weaponises the tension. The flushed cheeks and intent gaze read as passion for the alliance, and the foreign delegate responds to the magnetic energy by becoming surprisingly cooperative. Terms swing favourably and both sides leave satisfied.",
    "critical_success": "{worker_name} turns smouldering distraction into the most seductive diplomacy the court has ever witnessed. Every loaded pause, every 'accidental' touch during the document signing, every whispered aside — the foreign delegation is utterly charmed. They concede points they'd normally die on, convinced they're forging a deeply personal alliance."
  },
  "earnings": {
    "success": "50 + skill * 2",
    "critical_success": "50 + skill * 3",
    "mediocre": "skill",
    "failure": "-(roll - skill)"
  },
  "consequences": {
    "failure": { "energy": -4, "joy": -2, "rebelliousness": 1, "reputation": -15, "libido": -5 },
    "mediocre": { "energy": -4, "joy": -1, "reputation": -5, "libido": -5 },
    "success": { "energy": -4, "joy": 2, "reputation": 20, "libido": -10 },
    "critical_success": { "energy": -3, "joy": 3, "reputation": 30, "libido": -10 }
  },
  "story_image": "ambassador_libido20",
  "failure_image": "ambassador_libido20_failure",
  "positive_traits": { "Nympho": 4, "High Libido": 3, "Smooth Talker": 4, "Magnetic": 3 },
  "negative_traits": { "Nervous": 4, "Shy": 3 },
  "trait_msg_success": "{worker_name}'s {trait} turns desperate distraction into irresistible diplomacy.",
  "trait_msg_failure": "{worker_name}'s {trait} made the loss of focus impossible to hide."
}
```

- [ ] **Step 2: Add libido stories to other castle professions**

Check which other professions exist in the castle section and add one story each, following the same pattern. The implementer should read the castle section (starts at line ~5043) to identify all professions before adding stories. Each story must:
- Use `skill_options` matching the profession's existing skills
- Use `stat_requirements.libido: 20`
- Have `nsfw_only: true`
- Include `-10 libido` on success/critical_success, `-5` on failure/mediocre
- Use a unique `story_image` name (e.g., `courtesan_libido20`, `spy_libido20`)

- [ ] **Step 3: Validate JSON and commit**

```bash
python -c "import json; json.load(open('game/data/buildings/building_types.json', encoding='utf-8')); print('JSON valid')"
git add game/data/buildings/building_types.json
git commit -m "feat: add high-libido daily stories to castle professions"
```

---

## Summary of all new stories

| Building | Profession | Story ID | skill_options |
|----------|-----------|----------|---------------|
| Brothel | Prostitute | `prostitute_libido20_heat` | Sex |
| Brothel | Masseuse | `masseuse_libido20_oiled_surrender` | Hand |
| Brothel | Expert Attendant | `ea_libido20_unhinged_session` | Sex, BDSM, Special |
| Brothel | Stripper | `stripper_libido20_stage_fever` | Striptease |
| Brothel | Service | `service_libido20_distracted_shift` | Charm |
| Restaurant | Service | `service_libido20_flirty_floor` | Charm |
| Restaurant | Cook | `cook_libido20_kitchen_steam` | Service |
| Adventurer's Guild | Adventurer | `adventurer_libido20_reckless_hunt` | Combat, Agility |
| Tavern | Bartender | `bartender_libido20_uninhibited_shift` | Charm, Service |
| Tavern | Entertainer | `entertainer_libido20_provocative_show` | Charm |
| Casino | Dealer | `dealer_libido20_heated_table` | Service |
| Casino | Guard | `guard_libido20_tense_patrol` | Combat |
| Castle | Ambassador | `ambassador_libido20_charged_diplomacy` | Charm, Clever |
| Castle | Others | TBD by implementer based on profession list | Match existing |

### Mechanical consistency (all stories):
- `weight: 20` (fires often when eligible)
- `stat_requirements.libido: 20`
- `nsfw_only: true`
- `difficulty_modifier: 10`
- Success/critical_success consequences: `libido: -10`
- Failure/mediocre consequences: `libido: -5`

### rest_nsfw changes:
- All 5 `rest_nsfw_relief_*` entries: `libido: -3` → `libido: -10`
