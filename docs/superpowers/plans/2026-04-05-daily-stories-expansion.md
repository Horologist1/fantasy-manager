# Daily Stories Expansion - Restaurant, Tavern, Casino

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 15 new daily stories (5 per building) to Restaurant, Tavern, and Casino, including NSFW variants, to bring them closer to the quality level of Brothel and Adventurer's Guild.

**Architecture:** All stories live in `game/data/buildings/building_types.json` as entries in each profession's `daily_stories` array. No code changes needed - only JSON data additions following the existing schema.

**Tech Stack:** JSON data files, Ren'Py engine (reads the JSON at runtime)

---

## File Structure

- **Modify:** `game/data/buildings/building_types.json`
  - Restaurant section (starts at line ~2009, professions: service, cook, manager)
  - Tavern section (starts at line ~3595, professions: bartender, entertainer, manager)
  - Casino section (starts at line ~4072, professions: dealer, guard, casino_server, manager)

No new files are created. All changes are additions to existing `daily_stories` arrays within the JSON.

---

## Story Schema Reference

Every new story must follow this exact structure:

```json
{
  "id": "unique_snake_case_id",
  "weight": 5,
  "report": "Short Title for Daily Report",
  "skill_options": ["SkillName"],
  "trait_success": "Message when trait helps. Uses {worker_name} and {trait}.",
  "earnings": {
    "failure": "-(roll - skill)",
    "mediocre": "skill",
    "success": "50 + skill",
    "critical_success": "50 + skill * 2"
  },
  "story_image": "image_tag",
  "failure_image": "image_tag_failure",
  "descriptions": {
    "failure": "2-3 sentence failure narrative using {worker_name}.",
    "mediocre": "2-3 sentence mediocre narrative.",
    "success": "2-3 sentence success narrative.",
    "critical_success": "2-3 sentence critical success narrative."
  },
  "consequences": {
    "failure": { "energy": -3, "joy": -1, "rebelliousness": 1, "reputation": -5 },
    "mediocre": { "energy": -3, "joy": -1, "rebelliousness": 1, "reputation": -5 },
    "success": { "energy": -3, "joy": 1, "reputation": 5 },
    "critical_success": { "energy": -2, "joy": 3, "reputation": 10 }
  },
  "nsfw_only": false,
  "positive_traits": { "TraitName": 3 },
  "trait_msg_success": "Same as trait_success.",
  "trait_msg_failure": "{worker_name}'s {trait} didn't help this time.",
  "negative_traits": {}
}
```

NSFW stories add `"nsfw_only": true` and may include `"stat_requirements": { "libido": 15 }`.

Stories with gender requirements add `"worker_gender_requirement": "female"` or `"male"`.

---

### Task 1: Restaurant - New Stories (3 SFW + 1 NSFW)

**Files:**
- Modify: `game/data/buildings/building_types.json` (Restaurant section, lines ~2009-2375)

- [ ] **Step 1: Add "Noble's Private Dinner" to Server profession**

Insert after the `service_clumsy_paperwork_recovery` story (after line ~2130), inside the `daily_stories` array of the `service` profession:

```json
{
  "id": "service_noble_dinner_restaurant",
  "weight": 2,
  "report": "Noble's Private Dinner",
  "skill_options": ["Charm"],
  "trait_success": "The noble is captivated by {worker_name}'s {trait} during the private dinner service.",
  "earnings": {
    "failure": "-(roll - skill)",
    "mediocre": "skill",
    "success": "50 + skill * 2",
    "critical_success": "50 + skill * 3"
  },
  "story_image": "service_story1_restaurant",
  "failure_image": "service_story1_restaurant_failure",
  "descriptions": {
    "failure": "{worker_name} fumbles the private dinner service for a visiting noble. Pours wine clumsily, serves courses out of order, and seems flustered by the aristocrat's sharp gaze. The noble leaves in a huff, loudly declaring the establishment unworthy of their patronage.",
    "mediocre": "{worker_name} manages the noble's private dinner without disaster, but the service lacks the elegance expected. The wine is slightly too warm, the timing between courses is off, and the noble departs with a polite but clearly disappointed nod.",
    "success": "{worker_name} delivers impeccable service for the noble's private dinner. Every course arrives at the perfect moment, wine is poured with grace, and {worker_name}'s attentive yet unobtrusive presence makes the aristocrat feel genuinely pampered. A generous tip follows.",
    "critical_success": "{worker_name} transforms the private dinner into an unforgettable experience. Anticipates the noble's every desire before it's spoken, pairs wines flawlessly with each course, and maintains such refined composure that the aristocrat insists on booking a recurring reservation and recommends the restaurant to their entire circle."
  },
  "consequences": {
    "failure": { "energy": -3, "joy": -2, "rebelliousness": 1, "reputation": -8 },
    "mediocre": { "energy": -3, "joy": -1, "reputation": -3 },
    "success": { "energy": -3, "joy": 2, "reputation": 8 },
    "critical_success": { "energy": -2, "joy": 3, "reputation": 15 }
  },
  "nsfw_only": false,
  "positive_traits": { "Elegant": 4, "Graceful": 3, "Beautiful": 3 },
  "trait_msg_success": "The noble is captivated by {worker_name}'s {trait} during the private dinner service.",
  "trait_msg_failure": "{worker_name}'s {trait} didn't help this time.",
  "negative_traits": { "Clumsy": 3, "Shy": 2 }
}
```

- [ ] **Step 2: Add "Kitchen Fire Crisis" to Cook profession**

Insert after the `cook_story2_restaurant` story (after line ~2256), inside the `daily_stories` array of the `cook` profession:

```json
{
  "id": "cook_fire_crisis_restaurant",
  "weight": 2,
  "report": "Kitchen Fire Crisis",
  "skill_options": ["Service"],
  "difficulty_modifier": -5,
  "trait_success": "{worker_name}'s {trait} proves decisive when the kitchen catches fire.",
  "earnings": {
    "failure": "-(roll - skill)",
    "mediocre": "skill",
    "success": "50 + skill",
    "critical_success": "50 + skill * 2"
  },
  "story_image": "cook_story1",
  "failure_image": "cook_story1_failure",
  "descriptions": {
    "failure": "{worker_name} panics when a grease fire erupts on the stove and spreads to the spice rack. Instead of smothering it, they throw water on the grease, making it worse. By the time it's contained, half the kitchen is scorched and {worker_name} has burns on their arms. The restaurant closes early.",
    "mediocre": "{worker_name} reacts slowly when flames leap from a pan to the overhead linens. Eventually manages to smother the fire with salt and damp cloths, but the delay means smoke fills the dining room, scaring off most customers. The kitchen is functional but damaged.",
    "success": "{worker_name} spots the fire the instant it flares and reacts with cool precision. Smothers the flames with a heavy lid, isolates the fuel source, and has the kitchen ventilated before smoke reaches the dining room. The evening continues with barely a disruption.",
    "critical_success": "{worker_name} handles the fire so calmly and efficiently that most diners never realize anything happened. Puts it out in seconds, improvises the remaining courses around the damaged station, and even jokes about it with the kitchen staff. The manager is deeply impressed."
  },
  "consequences": {
    "failure": { "energy": -5, "health": -8, "joy": -2, "rebelliousness": 1, "reputation": -10 },
    "mediocre": { "energy": -4, "health": -3, "joy": -1, "reputation": -5 },
    "success": { "energy": -4, "joy": 1, "reputation": 5 },
    "critical_success": { "energy": -3, "joy": 3, "reputation": 10, "relationship": 1 }
  },
  "nsfw_only": false,
  "positive_traits": { "Determined": 4, "Robust": 3, "Energetic": 3 },
  "trait_msg_success": "{worker_name}'s {trait} proves decisive when the kitchen catches fire.",
  "trait_msg_failure": "{worker_name}'s {trait} didn't help this time.",
  "negative_traits": { "Nervous": 4, "Clumsy": 3 }
}
```

- [ ] **Step 3: Add "Health Inspection" to Manager profession**

Insert after the `manager_restaurant` story (after line ~2324), inside the `daily_stories` array of the `manager` profession:

```json
{
  "id": "manager_health_inspection_restaurant",
  "weight": 2,
  "report": "Health Inspection",
  "skill_options": ["Clever"],
  "difficulty_modifier": -5,
  "trait_success": "{worker_name}'s {trait} impresses the health inspector.",
  "earnings": {
    "failure": "-(roll - skill) * 2",
    "mediocre": "skill",
    "success": "50 + skill",
    "critical_success": "50 + skill * 2"
  },
  "story_image": "manager_restaurant",
  "failure_image": "manager_restaurant_failure",
  "descriptions": {
    "failure": "{worker_name} is caught completely off guard when a royal health inspector arrives unannounced. The kitchen is a mess, storage records are incomplete, and {worker_name} can't answer basic questions about food sourcing. The inspector issues a formal warning that damages the restaurant's standing.",
    "mediocre": "{worker_name} handles the surprise inspection adequately but several minor violations are noted - a mislabeled container, a slightly disorganized cold storage. The inspector passes the restaurant conditionally, leaving a cloud of mediocrity hanging over the establishment.",
    "success": "{worker_name} greets the surprise inspector with composure and guides them through a well-organized kitchen. Records are up to date, storage is clean, and {worker_name} answers every question with confidence. The restaurant passes with a strong report.",
    "critical_success": "{worker_name} turns the surprise inspection into a showcase. Every detail is perfect - immaculate records, spotless facilities, and {worker_name}'s thorough knowledge of every ingredient's origin impresses the inspector so much they recommend the restaurant to the royal court."
  },
  "consequences": {
    "failure": { "energy": -4, "joy": -2, "reputation": -15 },
    "mediocre": { "energy": -4, "joy": -1, "reputation": -5 },
    "success": { "energy": -4, "joy": 2, "reputation": 10 },
    "critical_success": { "energy": -3, "joy": 3, "reputation": 20 }
  },
  "nsfw_only": false,
  "positive_traits": { "Clever": 4, "Sharp-Eyed": 3, "Hardworking": 3 },
  "trait_msg_success": "{worker_name}'s {trait} impresses the health inspector.",
  "trait_msg_failure": "{worker_name}'s {trait} didn't help this time.",
  "negative_traits": { "Lazy": 4, "Clumsy": 2 }
}
```

- [ ] **Step 4: Add NSFW "The Generous Tipper" to Server profession**

Insert after the new `service_noble_dinner_restaurant` story, inside the `daily_stories` array of the `service` profession:

```json
{
  "id": "service_generous_tipper_nsfw_restaurant",
  "weight": 2,
  "report": "The Generous Tipper",
  "skill_options": ["Charm"],
  "stat_requirements": { "libido": 15 },
  "trait_success": "The wealthy patron can't resist {worker_name}'s {trait}.",
  "earnings": {
    "failure": "-(roll - skill)",
    "mediocre": "skill",
    "success": "100 + skill * 2",
    "critical_success": "100 + skill * 3"
  },
  "story_image": "service_story1_restaurant",
  "failure_image": "service_story1_restaurant_failure",
  "descriptions": {
    "failure": "{worker_name} misreads the wealthy patron's intentions entirely. When the man suggests they 'continue the evening privately,' {worker_name} freezes up and stammers through an awkward rejection. The patron feels humiliated, leaves without paying his full bill, and the whole encounter leaves {worker_name} shaken and embarrassed.",
    "mediocre": "{worker_name} follows the wealthy patron to the private dining room after closing, but nerves get the better of them. The handjob is clumsy and rushed, {worker_name}'s grip too tight, the rhythm all wrong. The patron finishes with a grunt of mild satisfaction, leaves a decent tip, but clearly expected more from someone so attractive.",
    "success": "{worker_name} locks the private dining room door and kneels between the patron's legs with a confident smile. Works him slowly with both hands first, teasing, then takes him into their mouth with a steady rhythm that has the man gripping the tablecloth. The patron comes hard, gasping, and presses a heavy purse of gold into {worker_name}'s hand before leaving on unsteady legs.",
    "critical_success": "{worker_name} turns the after-hours encounter into something the patron will never forget. Starts by straddling his lap, grinding slowly while whispering exactly what they're going to do. Then drops to their knees and delivers such expert oral - deep, slow strokes with their tongue working the underside - that the patron has to bite his fist to keep quiet. He finishes twice before the night is over, and leaves an obscene amount of gold along with a standing invitation to his private estate."
  },
  "consequences": {
    "failure": { "energy": -2, "joy": -2, "rebelliousness": 1, "reputation": -5, "libido": -1 },
    "mediocre": { "energy": -2, "joy": 0, "libido": -3, "reputation": 0 },
    "success": { "energy": -3, "joy": 1, "libido": -5, "reputation": 3 },
    "critical_success": { "energy": -4, "joy": 2, "libido": -8, "reputation": 5, "relationship": 1 }
  },
  "nsfw_only": true,
  "positive_traits": { "Sexy Air": 5, "Beautiful": 4, "No Gag Reflex": 4, "Good Kisser": 3, "Open Minded": 3 },
  "trait_msg_success": "The wealthy patron can't resist {worker_name}'s {trait}.",
  "trait_msg_failure": "{worker_name}'s {trait} didn't help this time.",
  "negative_traits": { "Shy": 4, "Conservative": 5 }
}
```

- [ ] **Step 5: Validate JSON syntax**

Run: `python -c "import json; json.load(open('game/data/buildings/building_types.json', encoding='utf-8')); print('JSON valid')"`
Expected: `JSON valid`

- [ ] **Step 6: Commit Restaurant stories**

```bash
git add game/data/buildings/building_types.json
git commit -m "feat: add 4 new daily stories to Restaurant (3 SFW + 1 NSFW)"
```

---

### Task 2: Tavern - New Stories (3 SFW + 2 NSFW)

**Files:**
- Modify: `game/data/buildings/building_types.json` (Tavern section, lines ~3595-4047)

- [ ] **Step 1: Add "Bar Fight" to Bartender profession**

Insert after the `bartender_story1` story, inside the `daily_stories` array of the `bartender` profession:

```json
{
  "id": "bartender_bar_fight_tavern",
  "weight": 3,
  "report": "Bar Fight",
  "skill_options": ["Charm", "Service"],
  "difficulty_modifier": -3,
  "trait_success": "{worker_name}'s {trait} helps defuse the violent situation.",
  "earnings": {
    "failure": "-(roll - skill)",
    "mediocre": "skill",
    "success": "50 + skill",
    "critical_success": "50 + skill * 2"
  },
  "story_image": "bartender_story1",
  "failure_image": "bartender_story1_failure",
  "descriptions": {
    "failure": "{worker_name} watches helplessly as a disagreement between two drunk mercenaries explodes into a full tavern brawl. Tables shatter, bottles fly, and by the time the city guard arrives, the bar looks like a warzone. {worker_name} catches an elbow to the face trying to intervene too late, and the night's earnings are spent on repairs.",
    "mediocre": "{worker_name} tries to step between the fighters but gets shoved aside. Eventually talks the less drunk one into backing down, but not before a table and several chairs are destroyed. The other patrons clear out early, killing the evening's revenue.",
    "success": "{worker_name} reads the tension building between two groups of adventurers and acts before fists fly. Steps in with a firm voice and a free round, redirecting the aggression into a drinking contest instead. The night ends louder than usual, but profitable and with the furniture intact.",
    "critical_success": "{worker_name} handles the erupting brawl like a veteran peacekeeper. Catches the first thrown punch mid-swing by slamming a mug on the bar so hard the whole room freezes. Talks both sides down with a mix of humor and steel-eyed authority, then sells them twice as much ale as they'd normally drink. The tavern earns more than a usual night, and both groups leave as friends."
  },
  "consequences": {
    "failure": { "energy": -4, "health": -5, "joy": -2, "rebelliousness": 1, "reputation": -8 },
    "mediocre": { "energy": -4, "health": -2, "joy": -1, "reputation": -3 },
    "success": { "energy": -4, "joy": 1, "reputation": 5 },
    "critical_success": { "energy": -3, "joy": 3, "reputation": 10, "relationship": 1 }
  },
  "nsfw_only": false,
  "positive_traits": { "Strong": 4, "Confident": 3, "Robust": 3 },
  "trait_msg_success": "{worker_name}'s {trait} helps defuse the violent situation.",
  "trait_msg_failure": "{worker_name}'s {trait} didn't help this time.",
  "negative_traits": { "Shy": 3, "Delicate": 3, "Meek": 4 }
}
```

- [ ] **Step 2: Add "Mysterious Stranger" to Bartender profession**

Insert after the new `bartender_bar_fight_tavern` story:

```json
{
  "id": "bartender_mysterious_stranger_tavern",
  "weight": 2,
  "report": "Mysterious Stranger",
  "skill_options": ["Charm"],
  "trait_success": "{worker_name}'s {trait} helps navigate the stranger's cryptic requests.",
  "earnings": {
    "failure": "-(roll - skill)",
    "mediocre": "skill",
    "success": "50 + skill * 2",
    "critical_success": "50 + skill * 3"
  },
  "story_image": "bartender_story1",
  "failure_image": "bartender_story1_failure",
  "descriptions": {
    "failure": "{worker_name} tries to serve the hooded stranger who appeared at closing time, but something about the figure's cold, unblinking stare makes every movement clumsy. The stranger orders a drink that doesn't exist, and when {worker_name} admits ignorance, the figure stands without a word and leaves a single copper coin on the bar - an insult that feels oddly threatening.",
    "mediocre": "{worker_name} serves the cloaked stranger adequately but can't crack their silence. The figure drinks alone, pays fairly, and vanishes into the night. {worker_name} finds a strange symbol scratched into the bar where they sat, but nothing comes of it.",
    "success": "{worker_name} engages the mysterious traveler with the right balance of curiosity and discretion. Over several drinks, the stranger opens up enough to share tales from distant lands and leaves a generous purse of foreign gold. The stories attract other patrons who stay late to listen.",
    "critical_success": "{worker_name} recognizes the cloaked figure as someone of real importance - a disguised noble, a wandering archmage, or perhaps something stranger. Through careful conversation and perfect hospitality, {worker_name} earns the stranger's trust and a significant reward, along with a cryptic promise that 'this establishment will be remembered when the time comes.'"
  },
  "consequences": {
    "failure": { "energy": -3, "joy": -2, "reputation": -3 },
    "mediocre": { "energy": -3, "joy": 0, "reputation": 0 },
    "success": { "energy": -3, "joy": 2, "reputation": 8 },
    "critical_success": { "energy": -2, "joy": 3, "reputation": 15 }
  },
  "nsfw_only": false,
  "positive_traits": { "Clever": 4, "Mystical": 3, "Wise": 3 },
  "trait_msg_success": "{worker_name}'s {trait} helps navigate the stranger's cryptic requests.",
  "trait_msg_failure": "{worker_name}'s {trait} didn't help this time.",
  "negative_traits": { "Nervous": 3, "Dumb": 3 }
}
```

- [ ] **Step 3: Add "Heckler in the Crowd" to Entertainer profession**

Insert after the `entertainer_story2_tavern` story, inside the `daily_stories` array of the `entertainer` profession:

```json
{
  "id": "entertainer_heckler_tavern",
  "weight": 3,
  "report": "Heckler in the Crowd",
  "skill_options": ["Charm"],
  "difficulty_modifier": -3,
  "trait_success": "{worker_name}'s {trait} turns the heckler into part of the show.",
  "earnings": {
    "failure": "-(roll - skill)",
    "mediocre": "skill",
    "success": "50 + skill * 2",
    "critical_success": "50 + skill * 3"
  },
  "story_image": "entertainer_story1_tavern",
  "failure_image": "entertainer_story1_tavern_failure",
  "descriptions": {
    "failure": "{worker_name} loses control of the room when a loud drunk starts mocking their performance. Every attempt to continue is drowned out by crude jokes and jeers. The heckler's friends join in, the crowd turns hostile, and {worker_name} leaves the stage humiliated, fighting back tears while the tavern's atmosphere is ruined for the night.",
    "mediocre": "{worker_name} tries to ignore the persistent heckler but the interruptions keep breaking the flow. Manages to finish the set but the energy in the room is flat. A few sympathetic patrons tip anyway, but most leave early, and {worker_name} feels drained and frustrated.",
    "success": "{worker_name} handles the heckler like a seasoned performer. When the drunk shouts an insult, {worker_name} fires back with a razor-sharp comeback that gets the whole tavern roaring with laughter. The heckler shrinks in his seat, and the crowd rallies behind {worker_name} for the rest of the night.",
    "critical_success": "{worker_name} doesn't just shut the heckler down - they turn him into the best part of the show. Every interruption becomes fuel for improvised comedy so brilliant that even the heckler ends up laughing and buying rounds for the house. The crowd is in stitches, tips rain down, and the night becomes legendary tavern lore."
  },
  "consequences": {
    "failure": { "energy": -4, "joy": -3, "rebelliousness": 2, "reputation": -8 },
    "mediocre": { "energy": -4, "joy": -1, "reputation": -3 },
    "success": { "energy": -3, "joy": 2, "reputation": 8 },
    "critical_success": { "energy": -2, "joy": 4, "reputation": 15, "rebelliousness": -1 }
  },
  "nsfw_only": false,
  "positive_traits": { "Smooth Talker": 5, "Confident": 4, "Playful": 3, "Audacity": 3 },
  "trait_msg_success": "{worker_name}'s {trait} turns the heckler into part of the show.",
  "trait_msg_failure": "{worker_name}'s {trait} didn't help this time.",
  "negative_traits": { "Shy": 5, "Nervous": 4, "Meek": 3 }
}
```

- [ ] **Step 4: Add NSFW "Last Call Seduction" to Bartender profession**

Insert after the `bartender_mysterious_stranger_tavern` story:

```json
{
  "id": "bartender_last_call_nsfw_tavern",
  "weight": 2,
  "report": "Last Call Seduction",
  "skill_options": ["Charm"],
  "stat_requirements": { "libido": 15 },
  "trait_success": "{worker_name}'s {trait} makes the late-night encounter irresistible.",
  "earnings": {
    "failure": "-(roll - skill)",
    "mediocre": "skill",
    "success": "100 + skill * 2",
    "critical_success": "100 + skill * 3"
  },
  "story_image": "bartender_story1",
  "failure_image": "bartender_story1_failure",
  "descriptions": {
    "failure": "{worker_name} tries to reciprocate when the last patron - a handsome mercenary - leans across the bar and brushes their hand. But the nervous fumbling that follows is painful. {worker_name} knocks over a bottle reaching for them, the kiss is all teeth, and by the time they get behind the bar together the mood is dead. The mercenary leaves with an apologetic smile and {worker_name} cleans up alone, frustrated and unsatisfied.",
    "mediocre": "{worker_name} lets the attractive stranger stay past closing. They end up pressed against the back wall of the stockroom, kissing hungrily, but it's rushed and awkward. The stranger's hands are rough and impatient, {worker_name} can't find a comfortable angle, and the whole thing ends with a quick, unsatisfying fuck standing up between the ale barrels. The stranger leaves a few coins on the bar.",
    "success": "{worker_name} has been eyeing the dark-haired regular all evening, and when the last patron leaves, neither pretends there's any other reason to stay. They come together behind the bar, {worker_name} pressed against the counter, the stranger's mouth hot on their neck while hands work clothing loose. {worker_name} wraps their legs around the stranger's waist and they fuck right there, slow and deep, the empty tavern echoing with gasps. Afterward, the stranger leaves a heavy purse and a promise to come back tomorrow.",
    "critical_success": "{worker_name} doesn't even wait for the door to close behind the last customer. Pulls the muscular traveler behind the bar by their collar and kisses them hard. What follows is an hour of increasingly intense sex - bent over the bar, on the floor between the tables, against the stockroom door. {worker_name} rides them until they're both shaking, then lets the traveler take them from behind while they grip the bar rail. The stranger is so thoroughly satisfied they leave enough gold to cover the tavern's earnings for a week, and word of the tavern's 'hospitality' brings curious new patrons."
  },
  "consequences": {
    "failure": { "energy": -2, "joy": -2, "libido": -1, "rebelliousness": 1 },
    "mediocre": { "energy": -3, "joy": 0, "libido": -3 },
    "success": { "energy": -4, "joy": 2, "libido": -6, "reputation": 3 },
    "critical_success": { "energy": -5, "joy": 3, "libido": -10, "reputation": 5, "relationship": 1 }
  },
  "nsfw_only": true,
  "positive_traits": { "Sexy Air": 5, "Beautiful": 4, "High Libido": 3, "Open Minded": 3, "Nympho": 3 },
  "trait_msg_success": "{worker_name}'s {trait} makes the late-night encounter irresistible.",
  "trait_msg_failure": "{worker_name}'s {trait} didn't help this time.",
  "negative_traits": { "Conservative": 5, "Shy": 4, "Low Libido": 3 }
}
```

- [ ] **Step 5: Add NSFW "Private Performance" to Entertainer profession**

Insert after the `entertainer_heckler_tavern` story:

```json
{
  "id": "entertainer_private_performance_nsfw_tavern",
  "weight": 1,
  "report": "Private Performance",
  "skill_options": ["Charm"],
  "stat_requirements": { "libido": 15 },
  "trait_success": "The noble is utterly entranced by {worker_name}'s {trait}.",
  "earnings": {
    "failure": "-(roll - skill)",
    "mediocre": "skill * 2",
    "success": "100 + skill * 2",
    "critical_success": "100 + skill * 3"
  },
  "story_image": "entertainer_story2_tavern",
  "failure_image": "entertainer_story2_tavern_failure",
  "descriptions": {
    "failure": "{worker_name} accepts the noble's invitation to perform privately in the upstairs room, but freezes when the noble's hand slides up their thigh mid-song. The performance crumbles, {worker_name} stammers through an excuse and flees the room. The noble is furious at being refused after paying for the 'full experience' and threatens to ruin the tavern's reputation.",
    "mediocre": "{worker_name} dances for the noble in the private room, letting clothes fall away piece by piece. But when the noble pulls them onto their lap, {worker_name}'s rhythm falters. The sex that follows is functional but uninspired - the noble gets off, {worker_name} goes through the motions. The payment is fair but the noble won't be requesting a private show again.",
    "success": "{worker_name} gives the noble exactly the escalation they're craving. Starts with a slow, teasing dance, peeling away garments one by one while maintaining eye contact. When the noble can't take any more, {worker_name} straddles them in the velvet chair and rides them with the same rhythm as the dance - controlled, sensual, building. The noble comes undone completely, moaning {worker_name}'s name, and pays triple the agreed price.",
    "critical_success": "{worker_name} delivers a private performance that blurs the line between art and pure carnality. The dance starts slow, hypnotic, every movement designed to drive the noble mad with want. By the time {worker_name} is naked and straddling the noble, the aristocrat is begging. What follows is an extended session where {worker_name} controls every moment - riding, grinding, whispering filth into the noble's ear between kisses. The noble climaxes so hard they nearly pass out, then books {worker_name} for every visit to the city, paying an exclusive retainer that dwarfs normal earnings."
  },
  "consequences": {
    "failure": { "energy": -3, "joy": -3, "rebelliousness": 2, "reputation": -5, "libido": -1 },
    "mediocre": { "energy": -3, "joy": 0, "libido": -4, "reputation": 0 },
    "success": { "energy": -4, "joy": 2, "libido": -7, "reputation": 5 },
    "critical_success": { "energy": -5, "joy": 4, "libido": -10, "reputation": 10, "relationship": 1 }
  },
  "nsfw_only": true,
  "positive_traits": { "Sexy Air": 5, "Graceful": 4, "Exhibitionist": 4, "Beautiful": 3, "Flexible": 3 },
  "trait_msg_success": "The noble is utterly entranced by {worker_name}'s {trait}.",
  "trait_msg_failure": "{worker_name}'s {trait} didn't help this time.",
  "negative_traits": { "Conservative": 5, "Shy": 4, "Stiff": 3 }
}
```

- [ ] **Step 6: Add "Rowdy Night" to Manager profession**

Insert after the `manager_tavern` story, inside the `daily_stories` array of the `manager` profession:

```json
{
  "id": "manager_rowdy_night_tavern",
  "weight": 2,
  "report": "Rowdy Night",
  "skill_options": ["Clever"],
  "difficulty_modifier": -3,
  "trait_success": "{worker_name}'s {trait} keeps the chaos profitable.",
  "earnings": {
    "failure": "-(roll - skill)",
    "mediocre": "skill",
    "success": "50 + skill * 2",
    "critical_success": "50 + skill * 3"
  },
  "story_image": "manager_tavern",
  "failure_image": "manager_tavern_failure",
  "descriptions": {
    "failure": "{worker_name} is overwhelmed when three adventuring parties, a merchant caravan, and a dwarven wedding all arrive on the same night. The kitchen runs out of food, the bar runs dry, staff are run ragged, and a fistfight breaks out over the last table. The night ends in chaos, broken furniture, and furious customers.",
    "mediocre": "{worker_name} struggles to keep up with the massive crowd. Manages to prevent total disaster through frantic improvisation, but service is slow, some customers leave without ordering, and the staff is exhausted and resentful. The earnings are decent but the cost in morale is high.",
    "success": "{worker_name} rises to the occasion on the busiest night in recent memory. Reorganizes staff on the fly, opens the overflow seating area, and negotiates with the kitchen to stretch supplies. The night is hectic but profitable, and every customer leaves having had a good time.",
    "critical_success": "{worker_name} orchestrates the chaotic night like a master conductor. Somehow finds room for everyone, keeps the drinks flowing, turns potential conflicts into drinking competitions, and even gets the dwarven wedding party to lead the whole tavern in song. The night's earnings are extraordinary and the staff is buzzing with energy rather than exhaustion."
  },
  "consequences": {
    "failure": { "energy": -5, "joy": -2, "rebelliousness": 1, "reputation": -10 },
    "mediocre": { "energy": -5, "joy": -1, "reputation": -3 },
    "success": { "energy": -5, "joy": 2, "reputation": 10 },
    "critical_success": { "energy": -4, "joy": 4, "reputation": 20 }
  },
  "nsfw_only": false,
  "positive_traits": { "Clever": 4, "Energetic": 4, "Charismatic": 3, "Hardworking": 3 },
  "trait_msg_success": "{worker_name}'s {trait} keeps the chaos profitable.",
  "trait_msg_failure": "{worker_name}'s {trait} didn't help this time.",
  "negative_traits": { "Lazy": 4, "Slow Learner": 3 }
}
```

- [ ] **Step 7: Validate JSON syntax**

Run: `python -c "import json; json.load(open('game/data/buildings/building_types.json', encoding='utf-8')); print('JSON valid')"`
Expected: `JSON valid`

- [ ] **Step 8: Commit Tavern stories**

```bash
git add game/data/buildings/building_types.json
git commit -m "feat: add 6 new daily stories to Tavern (3 SFW + 2 NSFW + 1 manager)"
```

---

### Task 3: Casino - New Stories (3 SFW + 2 NSFW)

**Files:**
- Modify: `game/data/buildings/building_types.json` (Casino section, lines ~4072-4517)

- [ ] **Step 1: Add "High Roller Arrives" to Dealer profession**

Insert after the `dealer_story1` story, inside the `daily_stories` array of the `dealer` profession:

```json
{
  "id": "dealer_high_roller_casino",
  "weight": 2,
  "report": "High Roller Arrives",
  "skill_options": ["Service"],
  "trait_success": "The high roller is impressed by {worker_name}'s {trait} at the table.",
  "earnings": {
    "failure": "-(roll - skill) * 2",
    "mediocre": "skill",
    "success": "100 + skill * 2",
    "critical_success": "100 + skill * 3"
  },
  "story_image": "dealer_story1",
  "failure_image": "dealer_story1_failure",
  "descriptions": {
    "failure": "{worker_name} fumbles badly when a legendary high roller takes a seat at their table with a mountain of gold. Misdeals twice, miscounts a payout, and the high roller's cold stare makes {worker_name}'s hands shake worse. The whale stands, declares the table 'beneath them,' and moves to a competitor's establishment, taking a fortune in potential earnings with them.",
    "mediocre": "{worker_name} handles the high roller's table competently but without the flair that big spenders expect. The dealing is clean but mechanical, the patter flat. The whale plays for an hour, wins modestly, and leaves without fanfare. A missed opportunity for the casino to shine.",
    "success": "{worker_name} delivers a masterful performance for the high roller. Smooth, rapid dealing, perfect payouts, and just enough charm to keep the whale engaged and betting bigger. The high roller has a thrilling night at the tables, loses a respectable sum gracefully, and tips {worker_name} handsomely while promising to return.",
    "critical_success": "{worker_name} gives the high roller the most exhilarating gambling experience of their life. Every deal is crisp perfection, the pace keeps the adrenaline pumping, and {worker_name}'s magnetic presence at the table draws a crowd of spectators. The whale bets recklessly, wins some spectacular hands, loses even more, and doesn't care because the thrill is worth every coin. The casino's take is enormous, and the high roller becomes a regular patron."
  },
  "consequences": {
    "failure": { "energy": -4, "joy": -2, "reputation": -12 },
    "mediocre": { "energy": -4, "joy": 0, "reputation": -2 },
    "success": { "energy": -4, "joy": 2, "reputation": 10 },
    "critical_success": { "energy": -3, "joy": 4, "reputation": 20 }
  },
  "nsfw_only": false,
  "positive_traits": { "Charming": 4, "Smooth Talker": 4, "Elegant": 3, "Clever": 3 },
  "trait_msg_success": "The high roller is impressed by {worker_name}'s {trait} at the table.",
  "trait_msg_failure": "{worker_name}'s {trait} didn't help this time.",
  "negative_traits": { "Nervous": 4, "Clumsy": 3 }
}
```

- [ ] **Step 2: Add "Card Counting Suspect" to Dealer profession**

Insert after the new `dealer_high_roller_casino` story:

```json
{
  "id": "dealer_card_counter_casino",
  "weight": 2,
  "report": "Card Counting Suspect",
  "skill_options": ["Service"],
  "difficulty_modifier": -3,
  "trait_success": "{worker_name}'s {trait} helps identify the cheater's pattern.",
  "earnings": {
    "failure": "-(roll - skill) * 2",
    "mediocre": "skill",
    "success": "50 + skill * 2",
    "critical_success": "50 + skill * 3"
  },
  "story_image": "dealer_story1",
  "failure_image": "dealer_story1_failure",
  "descriptions": {
    "failure": "{worker_name} notices a quiet player winning suspiciously often but can't figure out the method. Accuses them prematurely without evidence, causing a scene. The player turns out to be a minor noble who threatens legal action, and the casino has to comp their winnings plus damages to avoid scandal.",
    "mediocre": "{worker_name} suspects a player is counting cards but can't gather enough proof to act. Tries shuffling more frequently to disrupt them, which slows the table and annoys other players. The suspect eventually cashes out with modest winnings, and {worker_name} is left unsure whether they were right.",
    "success": "{worker_name} spots the card counter's tells - the subtle bet increases after favorable counts, the too-casual glances at the discard pile. Without causing a scene, {worker_name} adjusts the shuffle timing and deck penetration to neutralize the advantage, then quietly signals security. The counter is escorted out with their original buy-in and banned from returning.",
    "critical_success": "{worker_name} not only catches the card counter but identifies them as part of a larger team working multiple tables. By tracking their signaling patterns - a touch of the ear, a specific chip placement - {worker_name} maps the entire operation. Security removes the whole ring simultaneously, recovering thousands in stolen winnings. Management is deeply impressed."
  },
  "consequences": {
    "failure": { "energy": -4, "joy": -2, "reputation": -10 },
    "mediocre": { "energy": -4, "joy": -1, "reputation": -3 },
    "success": { "energy": -4, "joy": 2, "reputation": 8 },
    "critical_success": { "energy": -3, "joy": 3, "reputation": 15, "relationship": 1 }
  },
  "nsfw_only": false,
  "positive_traits": { "Sharp-Eyed": 5, "Clever": 4, "Determined": 3 },
  "trait_msg_success": "{worker_name}'s {trait} helps identify the cheater's pattern.",
  "trait_msg_failure": "{worker_name}'s {trait} didn't help this time.",
  "negative_traits": { "Dumb": 4, "Lazy": 3 }
}
```

- [ ] **Step 3: Add "Theft Attempt" to Guard profession**

Insert after the `guard_story2_casino` story, inside the `daily_stories` array of the `guard` profession:

```json
{
  "id": "guard_theft_attempt_casino",
  "weight": 2,
  "report": "Theft Attempt",
  "skill_options": ["Combat"],
  "difficulty_modifier": -5,
  "trait_success": "{worker_name}'s {trait} is crucial in stopping the heist.",
  "earnings": {
    "failure": "-(roll - skill) * 2",
    "mediocre": "skill",
    "success": "50 + skill * 2",
    "critical_success": "50 + skill * 3"
  },
  "story_image": "guard_story1_casino",
  "failure_image": "guard_story1_casino_failure",
  "descriptions": {
    "failure": "{worker_name} is caught completely off guard when a coordinated theft hits the casino's chip vault. A distraction at the main floor draws {worker_name} away from their post, and by the time they realize the ruse, the thieves have vanished with a chest of high-value chips. The loss is substantial and {worker_name} takes a beating from the getaway muscle.",
    "mediocre": "{worker_name} spots the thieves too late - they've already grabbed a handful of chips from behind the exchange counter. Gives chase and manages to tackle one of the three, recovering some of the stolen goods, but the other two escape into the crowd. Better than nothing, but the casino still takes a hit.",
    "success": "{worker_name} notices the suspicious coordination between three 'patrons' casing the chip vault and acts before they strike. Positions strategically, waits for the attempt, then intercepts the ringleader mid-grab. The other two flee empty-handed when they see their leader pinned. All stolen property is recovered and the would-be thief is handed to the city guard.",
    "critical_success": "{worker_name} doesn't just stop the theft - they set a trap. After noticing the casing pattern days ago, {worker_name} lets the thieves think they have an opening, then springs the ambush with perfect timing. All three are caught with evidence, the recovered intel reveals planned hits on other establishments, and the city guard pays a bounty for dismantling the ring."
  },
  "consequences": {
    "failure": { "energy": -5, "health": -8, "joy": -2, "rebelliousness": 1, "reputation": -12 },
    "mediocre": { "energy": -4, "health": -3, "joy": -1, "reputation": -3 },
    "success": { "energy": -4, "health": -1, "joy": 2, "reputation": 10 },
    "critical_success": { "energy": -3, "joy": 4, "reputation": 20, "relationship": 1 }
  },
  "nsfw_only": false,
  "positive_traits": { "Sharp-Eyed": 5, "Clever": 4, "Strong": 3, "Determined": 3 },
  "trait_msg_success": "{worker_name}'s {trait} is crucial in stopping the heist.",
  "trait_msg_failure": "{worker_name}'s {trait} didn't help this time.",
  "negative_traits": { "Lazy": 4, "Dumb": 3, "Clumsy": 3 }
}
```

- [ ] **Step 4: Add NSFW "Winner's Reward" to Dealer profession**

Insert after the `dealer_card_counter_casino` story:

```json
{
  "id": "dealer_winners_reward_nsfw_casino",
  "weight": 1,
  "report": "Winner's Reward",
  "skill_options": ["Service"],
  "stat_requirements": { "libido": 15 },
  "trait_success": "The winner can't take their eyes off {worker_name}'s {trait}.",
  "earnings": {
    "failure": "-(roll - skill)",
    "mediocre": "skill * 2",
    "success": "100 + skill * 2",
    "critical_success": "100 + skill * 3"
  },
  "story_image": "dealer_story1",
  "failure_image": "dealer_story1_failure",
  "descriptions": {
    "failure": "{worker_name} accepts the big winner's invitation to 'help celebrate' in the VIP suite, but the reality is awkward. The winner is too drunk to perform and {worker_name} spends an uncomfortable hour trying to coax life into a situation that isn't happening. Eventually gives up, receives a fraction of the promised tip, and slinks back to the floor feeling used and foolish.",
    "mediocre": "{worker_name} follows the flush-with-winnings gambler to the private suite above the casino. The sex is perfunctory - the winner is too excited about their gold to focus on {worker_name}, rushing through the act. A quick blowjob, a few minutes of distracted thrusting, and it's over. The tip is adequate but {worker_name} feels more like a prop in someone else's celebration than a participant.",
    "success": "{worker_name} celebrates the winner's big night in the upstairs suite with enthusiasm that matches the gambler's euphoria. Pushes them onto the silk-sheeted bed, strips slowly while the winner watches with hungry eyes, then climbs on top and rides them with a gambler's own sense of rhythm - slow when they want fast, fast when they're about to finish, edging them until they're begging. When they finally come, it's explosive. The winner empties a sizable portion of their winnings onto the nightstand.",
    "critical_success": "{worker_name} turns the post-victory celebration into the winner's greatest prize of the night. Starts in the suite's private bath, washing the winner with teasing hands that linger everywhere. Then leads them dripping to the bed where {worker_name} puts on a show - touching themselves while the winner watches, desperate. When {worker_name} finally lets the winner inside, the sex is intense and prolonged, {worker_name} matching every thrust with rolling hips and breathless moans. They fuck until dawn, the winner spending themselves three times. The gambler leaves half their winnings behind and tells everyone the casino's 'VIP experience' is worth any bet."
  },
  "consequences": {
    "failure": { "energy": -3, "joy": -2, "libido": -1, "rebelliousness": 1, "reputation": -3 },
    "mediocre": { "energy": -3, "joy": 0, "libido": -3 },
    "success": { "energy": -4, "joy": 2, "libido": -6, "reputation": 5 },
    "critical_success": { "energy": -5, "joy": 3, "libido": -10, "reputation": 8, "relationship": 1 }
  },
  "nsfw_only": true,
  "positive_traits": { "Sexy Air": 5, "Beautiful": 4, "High Libido": 3, "Nympho": 3, "Open Minded": 3 },
  "trait_msg_success": "The winner can't take their eyes off {worker_name}'s {trait}.",
  "trait_msg_failure": "{worker_name}'s {trait} didn't help this time.",
  "negative_traits": { "Conservative": 5, "Shy": 4, "Low Libido": 3 }
}
```

- [ ] **Step 5: Add NSFW "Champagne Room" to Casino Server profession**

Insert after the `service_clumsy_paperwork_casino_server` story, inside the `daily_stories` array of the `casino_server` profession:

```json
{
  "id": "server_champagne_room_nsfw_casino",
  "weight": 1,
  "report": "Champagne Room",
  "skill_options": ["Charm"],
  "stat_requirements": { "libido": 15 },
  "worker_gender_requirement": "female",
  "trait_success": "The VIP is completely captivated by {worker_name}'s {trait}.",
  "earnings": {
    "failure": "-(roll - skill)",
    "mediocre": "skill * 2",
    "success": "100 + skill * 2",
    "critical_success": "100 + skill * 3"
  },
  "story_image": "service_story1_casino",
  "failure_image": "service_story1_casino_failure",
  "descriptions": {
    "failure": "{worker_name} is summoned to the champagne room to serve a group of wealthy VIPs, but when their hands start wandering under her skirt, she flinches and pulls away. The VIPs mock her for being 'too uptight for this kind of work' and demand a different server. {worker_name} returns to the floor humiliated, the VIPs refuse to tip, and management is not pleased.",
    "mediocre": "{worker_name} serves champagne to the VIPs while their hands roam freely over her body. She lets one pull her onto his lap and grind against her while she pours refills, and gives another a hasty handjob under the table when he insists. It's mechanical and joyless, but the VIPs tip decently for the compliance if not the enthusiasm.",
    "success": "{worker_name} works the champagne room like she owns it. Pours drinks while perched on a VIP's knee, letting his hands explore under her uniform. When the richest one beckons her closer, she straddles him and rides him right there in the booth while the others watch and throw gold coins. Her moans are genuine enough to drive the whole room wild, and two more VIPs want their turn. She handles them all with a smile, collecting a small fortune in tips.",
    "critical_success": "{worker_name} transforms the champagne room into her personal stage. Starts by serving drinks in increasingly provocative poses, letting the VIPs bid for her attention. The winner gets a slow, devastating lap dance that ends with {worker_name} sinking onto him while the others watch in awe. She fucks him senseless while maintaining eye contact with the rest, then works her way through every man in the room who can match the price. By the end, she's dripping with sweat and satisfaction, surrounded by thoroughly ruined aristocrats and enough gold to fund the casino for a week."
  },
  "consequences": {
    "failure": { "energy": -2, "joy": -3, "rebelliousness": 2, "reputation": -5, "libido": -1 },
    "mediocre": { "energy": -3, "joy": -1, "libido": -4, "reputation": 0 },
    "success": { "energy": -5, "joy": 2, "libido": -8, "reputation": 5 },
    "critical_success": { "energy": -6, "joy": 3, "libido": -12, "reputation": 10, "relationship": 1 }
  },
  "nsfw_only": true,
  "positive_traits": { "Sexy Air": 5, "Beautiful": 5, "Large Breasts": 3, "Exhibitionist": 4, "Nympho": 3, "Open Minded": 3 },
  "trait_msg_success": "The VIP is completely captivated by {worker_name}'s {trait}.",
  "trait_msg_failure": "{worker_name}'s {trait} didn't help this time.",
  "negative_traits": { "Conservative": 5, "Shy": 5, "Low Libido": 3 }
}
```

- [ ] **Step 6: Add "Whale Negotiation" to Manager profession**

Insert after the `manager_casino` story, inside the `daily_stories` array of the `manager` profession:

```json
{
  "id": "manager_whale_negotiation_casino",
  "weight": 2,
  "report": "Whale Negotiation",
  "skill_options": ["Clever"],
  "trait_success": "{worker_name}'s {trait} secures the deal with the whale.",
  "earnings": {
    "failure": "-(roll - skill) * 2",
    "mediocre": "skill * 2",
    "success": "100 + skill * 2",
    "critical_success": "100 + skill * 3"
  },
  "story_image": "manager_casino",
  "failure_image": "manager_casino_failure",
  "descriptions": {
    "failure": "{worker_name} botches negotiations with a legendary high roller looking for a new regular casino. Offers terms that are either too stingy or too generous - the whale sees through the amateurish approach and takes their fortune to a rival establishment. The missed revenue is staggering.",
    "mediocre": "{worker_name} negotiates acceptable terms with the wealthy gambler, but gives away too many concessions - free suites, unlimited drinks, higher table limits. The whale agrees to play regularly, but the margins on their patronage are razor-thin. Better than losing them entirely, but barely.",
    "success": "{worker_name} strikes a shrewd deal with the mega-gambler. Offers just enough luxury and exclusivity to seal the commitment while protecting the casino's margins. The whale gets their private table, premium service, and modest credit line, while the casino locks in a patron whose losses will far exceed the perks over time.",
    "critical_success": "{worker_name} plays the negotiation like a master game of cards. Reads the whale's ego perfectly, offering prestige over discounts - a named table, a portrait on the VIP wall, first-name recognition from all staff. The whale is so flattered they accept terms that heavily favor the casino and bring three wealthy friends to the next session. The deal becomes the most profitable patron agreement in the casino's history."
  },
  "consequences": {
    "failure": { "energy": -4, "joy": -2, "reputation": -10 },
    "mediocre": { "energy": -4, "joy": 0, "reputation": 3 },
    "success": { "energy": -4, "joy": 2, "reputation": 12 },
    "critical_success": { "energy": -3, "joy": 4, "reputation": 25 }
  },
  "nsfw_only": false,
  "positive_traits": { "Clever": 5, "Smooth Talker": 4, "Charming": 3, "Elegant": 3 },
  "trait_msg_success": "{worker_name}'s {trait} secures the deal with the whale.",
  "trait_msg_failure": "{worker_name}'s {trait} didn't help this time.",
  "negative_traits": { "Dumb": 4, "Nervous": 3, "Shy": 3 }
}
```

- [ ] **Step 7: Validate JSON syntax**

Run: `python -c "import json; json.load(open('game/data/buildings/building_types.json', encoding='utf-8')); print('JSON valid')"`
Expected: `JSON valid`

- [ ] **Step 8: Commit Casino stories**

```bash
git add game/data/buildings/building_types.json
git commit -m "feat: add 6 new daily stories to Casino (3 SFW + 2 NSFW + 1 manager)"
```

---

## Summary

| Building | Before | After | New SFW | New NSFW |
|----------|--------|-------|---------|----------|
| Restaurant | 7 | 11 | 3 | 1 |
| Tavern | 8 | 14 | 4 | 2 |
| Casino | 8 | 14 | 4 | 2 |
| **Total** | **23** | **39** | **11** | **5** |

### Key Improvements
- **Narrative quality:** Every new story has 2-3 sentence descriptions per outcome (vs 1 sentence in originals)
- **Trait diversity:** Each story uses specific, thematic positive/negative traits (not just generic Hardworking/Robust)
- **Consequence variety:** New stories use health, libido, relationship, and rebelliousness where appropriate (not just energy/joy/rep)
- **NSFW stories:** Explicit content matching Brothel tone, gated behind `nsfw_only: true` and `libido >= 15`
- **Weighted variety:** New stories at weight 1-3 provide rarer, more interesting events alongside the weight-5 daily grind
