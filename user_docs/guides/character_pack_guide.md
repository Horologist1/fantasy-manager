# Character Pack Guide

> The main, always up-to-date reference is the **Mods** tab of the online Field Guide: https://horologist1.github.io/fantasy-manager/guide/#mods (also in `field_guide.html` next to this file).

How to build a character pack for Fantasy Manager: a character with her images, traits, recruitment scene, story events and daily stories, all in one ZIP.

In a hurry? Read the [Quick Guide](character_pack_quickstart.md) first. A complete working example lives in `templates/character_pack/`.

---

## 1. What a character pack is

A character pack is **one ZIP** with a `game/` folder inside and a `README.txt` next to it. The same ZIP installs in two ways:

| Method | How | Uninstall |
|---|---|---|
| **In-game importer** (recommended, works on Android) | Main menu > Mods > Install mods > choose the ZIP, then restart | "Uninstall" button in the same screen |
| **Drag & drop** (PC) | Extract, drag `game` onto the game's main folder (the one with `Fantasy_Manager.exe`), choose "merge" | Delete the pack's files by hand |

A pack only **adds** files. It never replaces a file of the game. Players must use **one method only**: the importer refuses a pack whose events or traits already exist, so it also refuses one that was copied in by hand.

## 2. Folder layout

```
MyPack.zip
├── README.txt
└── game/
    ├── data/
    │   ├── workers/<name>.json                         characters
    │   ├── traits/<name>.json                          new traits
    │   ├── events/<name>.json                          story events
    │   ├── events/recruit/<name>.json                  recruitment scenes
    │   └── buildings/daily_story_extensions/<name>.json  daily stories
    └── images/workers/<Folder>/                        the character's images
```

Every part except the images is optional. A pack can be just a character, or just events for characters that are already in the game (a "content-only" pack).

Use your own, unique file names (`mira.json`, `events_mira.json`…). Two files with the same name would overwrite each other in a drag & drop install.

**Not accepted in character packs:** items, buildings (`data/buildings/*.json`), interactions, monthly conditions, `.rpy`/`.py` scripts. The importer skips them and shows "N extra file(s) excluded". To change those, use the devkit's *JSON override* or *manual* modes.

## 3. The character (`data/workers/*.json`)

A JSON list of characters. Start from `templates/character_pack/game/data/workers/mira.json`.

| Field | Notes |
|---|---|
| `name` | Unique in the whole game. Events find the character by this exact name. |
| `folder` | Image folder name under `images/workers/`. Letters, numbers, `_` and `-` only. |
| `gender` | `female` or `male`. |
| `nsfw` | `true` hides the character when the player has NSFW off. Missing means `true`. |
| `unique`, `encounter_only` | `true` for a named character met through recruitment, not sold at the market. |
| `cost`, `skills`, `traits`, `description`, `names_list`, `comfort_desired` | As in the base game's workers. Every trait listed must exist in the game or in your pack. |

Any other field is dropped with a warning ("Unrecognised worker fields omitted"). Procedural, monster and template workers are not supported.

**Images:** the folder must contain a profile image (`profile.png`, `profile (1).jpg`…). Every other image must follow the game's naming rules (`agility (3).jpg`, `rest_tavern (2).png`…), described in the Field Guide's image section. Images whose names match no slot (for example `ComfyUI_temp_00001_.png`) are never shown. Rename them or leave them out.

## 4. Traits (`data/traits/*.json`)

A JSON list of trait objects, each with a `name` that does **not exist yet** in the game. If the name already exists, the importer rejects the pack: otherwise your trait would silently replace the original.

- Race traits list the other races in `conflicts` (include `Human`).
- Set `"only_assigned": true` for traits that should only come from your character or your events. Without it, random recruits can roll the trait.
- Put the effect in the description so players can see it: `[+5 Agility, +3 Clever]`.

## 5. Recruitment scene (`data/events/recruit/*.json`)

Shown when the player recruits and your character is available.

- `"worker_name": "<exact name>"` and `"random_worker": false` tie the scene to your character.
- Choices that hire use `"effect": {"recruit_worker": true}`. `[event_worker]`, `[COST]` and `[actual_cost]` are replaced in the text.
- `id`: new and unique. By convention it starts with `event_recruit_`.

## 6. Story events (`data/events/*.json`)

Random events during the day: quests, rivalries, promotions.

```json
{
  "id": "mira_trailblazer_trial",
  "worker_name": "Mira",
  "worker_selection": "random",
  "building_type": ["adventurers_guild"],
  "max_occurrences": 1,
  "conditions": {"start_when": "has_worker:Mira"},
  "excluded_flags": {"mira_trailblazer_done": true},
  "choices": [{
    "option": "Send Mira to chart the passes.",
    "condition": "Agility", "threshold": 50,
    "message_success": "...", "message_failure": "...",
    "effect": {
      "success": {"add_trait": "Trailblazer", "event_flags": {"mira_trailblazer_done": true}},
      "failure": {"event_flags": {"mira_trailblazer_done": true}}
    }
  }]
}
```

- **Chains:** event 1 sets a flag with `event_flags`, event 2 starts with `"start_when": "has_flag:<flag>"`, and each event excludes its own "done" flag.
- **One roll per choice:** `condition` + `threshold` appear once. Writing them twice in the same choice makes the JSON invalid; the importer reports "a key written twice". For extra minimums use `skill_requirements` (below).
- `required_traits` + `"trait_visibility": "blocked"` + `blocked_message` show a choice that can't be picked yet.
- Daily event ids must **not** start with `event_recruit_`: the game removes those from the daily pool.

### Several skills, or no roll

`skill_requirements` asks for several minimums at once: only workers meeting **all** of them can take the choice (otherwise the option is shown locked).

| The choice has | Result |
|---|---|
| `condition` + `threshold` | the usual roll |
| `condition` + `skill_requirements` | minimums decide who may try; the roll uses `condition` |
| only `skill_requirements` | **no roll**: a qualifying worker always succeeds (flat effect, or the `success` block) |

```json
{"option": "Send someone who can fight and climb.",
 "skill_requirements": {"Combat": 70, "Agility": 55},
 "message_success": "[acting_worker] clears the pass.",
 "effect": {"money": 500}}
```

Not with `worker_selection: "none"`, `building_skill` or in recruitment scenes. NSFW skills need `"nsfw": true` on the event or choice. Requires a game version newer than 0.9.6.2t1.

### Conditions you can use

`start_when` / `stop_when` accept these, joined with ` AND ` / ` OR `:

`has_flag:x`, `flag_value:x=value`, `after_days_from_flag:x,days`, `has_worker:Name`, `not_has_worker:Name`, `has_folder_worker:Folder`, `not_has_folder_worker:Folder`, `after_days:N`, `before_days:N`, `after_date:d,m,y`, `exact_date:d,m`, `True`, `False`, and simple comparisons such as `money >= 5000` or `store.current_objective >= 7`.

Anything else (function calls, brackets, `__`) is rejected. The game would run it as code, and a pack must never be able to do that. For the same reason, `event_flags` values written as `"[...]"` are rejected, with one exception, described below.

**Delayed chains:** to make event 2 wait N days after event 1, event 1 sets `"event_flags": {"mira_day": "[calculate_total_days()]"}`, which stores today's day number. Event 2 then uses `"start_when": "after_days_from_flag:mira_day,7"`. That exact value is the only `"[...]"` value packs may use.

## 7. Daily stories (`data/buildings/daily_story_extensions/*.json`)

Extra stories for an existing job. They are added to the game's own stories and never replace them.

```json
{"daily_story_extensions": [{
  "building_id": "adventurers_guild",
  "profession_id": "adventurer",
  "merge_mode": "append",
  "daily_stories": [ { "id": "mira_trailblazer_route", "report": "Route Charting", ... } ]
}]}
```

- `merge_mode` must be `append` (missing means `append`).
- `report` is the story's **title** in the daily report: short (24 characters or fewer), with no `{worker_name}`.
- To make a story exclusive to your character, use `required_traits` with one of your `only_assigned` traits. The `worker_name` field has no effect on daily stories.
- Every story `id` must be new.

Buildings and jobs you can target:

| building_id | profession_id |
|---|---|
| `academy` | `academy_academics`, `academy_amatory`, `academy_artisan`, `academy_hospitality`, `rest` |
| `adventurers_guild` | `adventurer`, `boss_hunting`, `manager`, `monster_taming`, `rest`, `treasure_hunter` |
| `arena` | `arena_championship`, `arena_exhibition`, `arena_oil_chains`, `arena_pinup_barbarian`, `arena_proving`, `arena_spectacle`, `rest` |
| `brothel` | `expert_attendant`, `manager`, `masseuse`, `prostitute`, `rest`, `service`, `stripper` |
| `casino` | `casino_server`, `dealer`, `guard`, `manager`, `rest` |
| `governor_castle` | `ambassador`, `chamberlain`, `courtesan`, `guards`, `pleasure_servant`, `prisoner`, `rest`, `servant` |
| `restaurant` | `cook`, `manager`, `rest`, `service` |
| `tavern` | `bartender`, `entertainer`, `manager`, `rest`, `tavern_server` |

## 8. What the importer checks

Before installing, the importer shows a summary ("1 character / 3 events / 2 traits…") and rejects the pack, with the reason, if:

- a file is not valid JSON or repeats a key inside the same object;
- a trait, event id or story id already exists in the game or in another installed pack;
- a daily story targets a building or job that doesn't exist, or doesn't use `append`;
- a condition or flag value is something the game would run as code;
- a character has no profile image or uses an invalid field value.

**Name clashes:** if a character's name already exists, the importer can install it as "Name (Mod xxxxxx)". It then updates `worker_name`, `has_worker:` and `has_folder_worker:` in the pack's own events, so they keep working.

## 9. Testing your pack

1. Build or check it in the devkit (Create Mods). It runs the same checks.
2. Install it with the in-game importer and read the summary: every file you expect should be counted, and nothing should be "excluded" by accident.
3. Restart and **start a new game**.
4. To see your events quickly, give the character the stats they need and keep them in the building listed in `building_type`.

## 10. Common mistakes

| Mistake | Result | Fix |
|---|---|---|
| Daily stories placed in `data/events/` | Not loaded | Move them to `data/buildings/daily_story_extensions/` |
| A whole building file to add one job's stories | Replaces the building, breaks the game | Use a daily story extension with `append` |
| `condition`/`threshold` written twice in one choice | Only the last one counts; the importer rejects it | One skill check per choice |
| Extra fields like `image_folder` on the character | Ignored, with a warning | Use `folder` |
| Events for a character not in the pack or the game | They never trigger | Ship the character too, or remove the events |
| A race trait without `only_assigned` | Random recruits get the race | Add `"only_assigned": true` |
| `{worker_name}` in a story's `report` | Shows up literally | Use a short title |
