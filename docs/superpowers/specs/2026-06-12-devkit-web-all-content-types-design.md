# Devkit Web — Plan 2: All Content Types (Completion)

**Date:** 2026-06-12
**Status:** Approved (autonomous goal session)
**Builds on:** `2026-06-10-modding-devkit-web-design.md` + Plan 1 (Workers MVP, shipped)

## 1. Goal

Complete the devkit so non-technical users can author every moddable JSON
content type through guided recipes and section editors, with live validation
and save flows that match the game's actual loaders. After this plan, a modder
never has to hand-write JSON for: workers, traits, items, interactions, events,
recruitment events, daily stories, buildings.

## 2. Scope

**In:**
- Schemas + validation rules for: trait, item, interaction, event,
  recruit_event, daily_story (extension), building (+profession).
- Recipes: `permanent_trait`, `temporary_trait`; `consumable_item`,
  `equipment_item`, `quest_item`; `simple_interaction`,
  `trait_granting_interaction`, `worker_specific_interaction`;
  `daily_story_basic`, `daily_story_with_trait_roll` (mandatory Requirements
  step); `worker_specific_event`, `event_chain_2_steps`,
  `building_event_with_skill_check`, `recruitment_event`;
  `simple_building_type`, `add_profession_to_building`; `monster_worker`,
  `procedural_worker_template`.
- Section editors for every type via the existing generic editor engine.
- New field renderers: `object` (fixed-shape group), `list_of_objects`
  (repeatable subform), `dict_of_bools` (flags), `dict_of_objects`,
  upgraded `dict_of_numbers` (add/remove keys + key catalog).
- Save flows matching the game loaders:
  - arrays: `workers/`, `traits/`, `interactions/`, `events/`,
    `events/recruit/` (merge by `name` or `id`)
  - wrapper objects: `items/*.json` (`items` array, preserve
    `excluded_from_shops`), `buildings/*.json` (`building_types` array)
  - daily story extensions: `buildings/daily_story_extensions/*.json`
    (`daily_story_extensions` entries merged by `building_id`+`profession_id`,
    story upsert by `id` inside the entry)
- Catalog additions: `all_skills` (canonical 25 + building `skill_name` scan),
  `building_professions` meta (building → professions with names) for guided
  building/profession picking.
- Landing page redesign: tiles grouped per content type, each offering its
  recipes + "Edit existing". Replace all `prompt()` flows with in-page
  file/entry pickers.
- Round-trip tests: shipped game data validates clean per type.

**Out (unchanged from master design; later plans):** Whoremaster converter,
image utilities (rename / GIF→WebM / worker-from-folder), GitHub Pages / ZIP /
in-game distribution, schema-doc generation script.

## 3. Key facts from the game loaders (verified)

- `data/events/*.json` — arrays; recruitment pool reads only
  `data/events/recruit/*.json`; daily pool excludes prefix `event_recruit_`.
- `data/interactions/*.json`, `data/traits/*.json`, `data/workers/*.json` —
  arrays, appended (workers dedup by name).
- `data/items/*.json` — `{ items: [], excluded_from_shops: [] }`, both merged.
- `data/buildings/*.json` — `{ building_types: [] }` merged **by id, later
  file overrides whole building**. `data/buildings/daily_story_extensions/`
  merges stories into an existing building/profession with
  `merge_mode: upsert|append|replace_all` (default upsert by story id).
- choice `condition`: `null` | `"none"` | `"building_skill"` | a skill name;
  `threshold` is roll-under d100.
- Recruit events use extra keys: `dialogue`, `unlimited`, `random_worker`,
  `always_available`, `worker_filter`, `effect.recruit_worker`,
  `effect.cost_modifier`, `outcome_override`.
- `worker_gender_requirement` on pool events is ignored → validator warning.

`add_profession_to_building` therefore copies the live building entry and
appends a profession (override-by-id semantics); the recipe warns that the
output snapshots the base building.

## 4. Architecture decisions

- Keep the declarative schema DSL; add recursive validation via `item_fields`
  (for `list_of_objects` / `dict_of_objects`) and `fields` (for `object`).
- Recipes stay flat (one question per screen). Complex JSON (choices, four
  outcome branches) is produced by `build()` from simple answers; users
  fine-tune in the editor afterwards.
- Editors expose the full schema, sectioned; nested shapes render with the new
  field renderers.
- Every recipe `build()` emits **all keys for its type with neutral defaults**
  (standardization rule), except flags dicts which stay minimal per the guide.

## 5. Testing

- TDD per module (`node --test`, happy-dom for renderers).
- Per-recipe test: synthetic answers → `build()` → validates clean against its
  schema with real baked catalogs.
- Round-trip test per type: every shipped entry in `game/data/` validates with
  0 errors (warnings allowed).
- fs merge tests for wrapper files and daily-story-extension upsert.
