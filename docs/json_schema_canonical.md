# Canonical JSON Schemas (Frozen)

This document is the canonical reference for modding JSON structures in this project.
All templates and normalized files follow these defaults:

- `null` for optional scalar text/id fields
- `[]` for list fields
- `{}` for object maps
- `0` for numeric fields
- `false` for booleans

## Runtime Scope

Gameplay runtime reads from `game/data` and `game/images` via explicit path filters in script code.
Documentation and templates under `docs/` are not loaded by the game.

## Events

### Event object
- `id`, `description`
- `weight`, `limited`, `max_occurrences`, `cooldown_days`
- `event_probability`, `guaranteed`
- `worker_selection`
- `worker_gender_requirement` — **not used** by random/building event selection (`select_possible_events`); prefer daily story `worker_gender_requirement` or interaction `worker_gender`. Validators may warn if present.
- `player_gender_requirement` — optional; restricts event to manager gender: values `male`, `female`, or aliases `lord`, `lady`. Runtime maps **Lord** title → male, **Lady** (or other) → female, then compares to normalized requirement.
- `requires_assigned_worker`
- `required_building_worker_traits`
- `required_active_professions` (profession ids active in `servant_jobs`, e.g. `guard`)
- `forbidden_active_professions` (no assigned worker may have these active jobs)
- `required_building_worker_min_skill` (int; optional; uses `required_building_worker_skill` or building type `skill_name`)
- `required_building_worker_skill` (string; optional skill name for the min-skill gate)
- `building_type`
- `background_image`, `success_image`, `failure_image`
- `nsfw`
- `required_flags`, `excluded_flags`
- `conditions.start_when`, `conditions.stop_when`
- `choices`
- compatibility keys: `start_when`, `stop_when`

### Event choice object
- `option`, `condition`, `threshold`
- `required_traits`, `excluded_traits` — worker must have **all** listed required traits and **none** of the excluded ones (for worker-backed choices; see runtime for `worker_selection` edge cases).
- `required_trait` — **legacy / compatibility only**: single trait name string. At runtime it is merged into `required_traits`. **Prefer** `required_traits: ["TraitName"]` (even for one trait) in new content so choices stay consistent.
- `trait_visibility` (`hide` or `blocked`)
- `blocked_message`
- `message`, `message_success`, `message_failure`
- `message_failure_worker_effect_skipped` (optional string): when `restrict_worker_effects_to_filter` is true and **worker-scoped** outcome effects (e.g. `add_trait` to a filtered pool) are skipped because no worker matched `effect_worker_filter`, `building_skill` failures may use this text instead of `message_failure`.
- `restrict_worker_effects_to_filter` (bool): when `true` and `effect_worker_filter` has at least one constraint, worker-targeted parts of `effect` (energy/health, `skill_modifiers`, `joy`, `add_trait` resolution) only apply to workers who pass the filter. Global keys (`money`, `reputation`, `event_flags`, `custom`, etc.) still apply.
- `effect_worker_filter` (object, optional): constraints evaluated against the **acting/target worker** using that worker’s active job in `servant_jobs` for the relevant building, plus traits and optional min skill. Same profession/trait semantics as event-level gates:
  - `required_active_professions`, `forbidden_active_professions` (profession ids; `rest` / `unassigned` are inactive)
  - `required_traits`, `excluded_traits`; `required_trait` inside the filter object is honored as an extra required trait name if present
  - `min_skill` (int) or `required_building_worker_min_skill` (int); with `skill_name` or `required_building_worker_skill`, or else the building type’s `skill_name` when a building context exists
- `conditions.start_when`, `conditions.stop_when`
- `required_flags`, `excluded_flags`
- `effect`

### Event effect object
- Flat keys: `money`, `reputation`, `custom`, `event_flags`, `item_id`, `loot_rolls`, `worker_name`, `random_worker`, `add_trait`
- Branch keys: `success`, `failure`
- `success_chance` (optional number, **0.0–1.0**): used **only** when the choice has **no** `condition` and `effect` includes at least one of `success` / `failure` (pure probability path in `process_choice`). Compared to `random.random()`; effective chance is `max(success_chance, difficulty floor)`. **`1` means always success** in that path. On **skill checks** (`condition` = skill name) and **`building_skill`**, this field is **ignored** for rolls—omit it there to avoid implying it changes odds.
- `add_trait`: `name`, `duration`, `target`

## Interactions

### Interaction object
- `id`, `name`, `description`
- `interaction_level`, `interaction_type`
- `cost_energy`, `cost_money`
- `effect`
- `gender_filter` (manager): optional; `male` / `female` or `lord` / `lady` (normalized like event `player_gender_requirement`). Compared to canonical manager gender from `player_title`.
- `worker_gender`
- `categories`, `image`, `nsfw`
- `stat_requirements`
- `specific_workers`, `required_traits`, `excluded_traits` — worker must have **all** required traits and **none** of the excluded traits (interactions do not use `required_trait`; use `required_traits` only).
- `required_flags`, `excluded_flags`

### Interaction effect object
- `romance`, `relationship`, `joy`, `rebelliousness`, `libido`
- `flags.<flag_name>.value`, `flags.<flag_name>.duration`
- `add_trait`: string (trait name) or `{ "name": "...", "duration": 0 }` — adds trait to worker
- `remove_trait`: string (trait name) or `{ "name": "..." }` — removes trait from worker
- Flags maps are sparse by design: include only flags actually needed by the interaction.

## Buildings / Professions / Daily stories

### Building type object
- `id`, `name`, `skill_name`, `skill_description`
- `nsfw`
- `allowed_map_locations`
- `professions`

### Profession object
- `id`, `name`, `description`
- `nsfw`, `difficulty`
- `skills`
- `max_daily_workers`
- `staffing_penalty` (float, optional): earnings multiplier when **0** workers in this job; typical `<1` for “essential” roles.
- `staffing_bonus` (float, optional): earnings multiplier when **≥1** worker in this job; use `>1` only for explicit staffed bonuses.
- `presence_roll_bonus` (int, optional): per worker in this job, summed into building synergy; added to **d100 skill threshold** (not the die); clamped **±40** building-total; omit or `0` for no effect.
- `daily_story_count.base`, `daily_story_count.bonus_formula`
- `daily_stories`
- deterministic/no-roll convention: for `rest` and `academy_*`, keep `daily_story_count` explicit (usually `{ "base": 1, "bonus_formula": "0" }`) to guarantee one processing pass per worker/day.

### Daily story object
- `id`, `weight`, `report`, `description`
- `difficulty_modifier`
- `worker_gender_requirement`
- `player_gender_requirement` — optional; same values and Lord/Lady semantics as random events; filters daily story pool before weighted pick (with fallback if no story matches).
- `nsfw_only`
- `skill_options`, `event_image_skill_exclude`
- `positive_traits`, `negative_traits` (dict: trait → weight; affects **threshold** + message pick), `relevant_traits` (legacy list), `trait_msg_success`, `trait_msg_failure`, `trait_success`
- `required_traits`, `excluded_traits`, `stat_requirements`
- `descriptions.failure`, `descriptions.mediocre`, `descriptions.success`, `descriptions.critical_success`
- `earnings.failure`, `earnings.mediocre`, `earnings.success`, `earnings.critical_success` — evaluated with `skill`, `level`, **`roll`** (d100)
- `consequences.failure|mediocre|success|critical_success`
- consequence stat keys: `energy`, `health`, `joy`, `rebelliousness`, `romance`, `relationship`, `reputation`, `libido`, `obedience`
- consequence trait/item keys: `trait_chance` (list of `{ "trait": "...", "chance_percent": 1-100, "duration"?: 0 }`; guaranteed grant = 100%; `name` / `percent` aliases accepted), `trait_remove_chance` (same entry shape without `duration`; roll then remove if present), `give_item` (item_id string or `{ "item_id": "...", "quantity": 1 }`)
- `story_image`, `failure_image`
- `loot.rolls`, `loot.bonus_items`, `loot.monster_worker`, `loot.captured_worker`
- deterministic/no-roll usage (`rest`, `academy_*`): runtime consumes `description` (or `descriptions.success` fallback) and `consequences.success`; roll-dependent branches (`earnings.*`, `descriptions.failure|mediocre|critical_success`) are optional compatibility fields for those jobs.

## Items

### Root object
- `items`
- `excluded_from_shops`

### Item object
- `id`, `name`, `display_name`, `type`
- `effect.custom`, `effect.skill_modifiers`, `effect.attribute_modifiers`, `effect.daily_effects`
- `description`, `durability`, `price`, `weight`, `nsfw`

## Traits

### Trait object
- `name`, `conflicts`, `removes_traits`
- `modifiers`
- `description`, `nsfw`

### Trait modifiers object
- `skill_modifiers`, `attribute_caps`, `attribute_minimums`, `daily_effects`
- `earnings_multiplier`, `libido_max`, `libido_regeneration`

## SFW Rule

Libido-related fields remain present in JSON for schema consistency.
In SFW mode, gameplay logic must keep libido effects inactive at runtime.

## Event availability gates (random / non-recruit pool)

- `requires_assigned_worker`: at least one assigned worker in a matching owned building.
- `required_building_worker_traits`: one assigned worker in a matching owned building has **all** listed traits.
- `required_active_professions`: at least one assigned worker has an active job whose id is in the list (matches `servant_jobs`; not `rest`/`unassigned`).
- `forbidden_active_professions`: no assigned worker has an active job in the list.
- `required_building_worker_min_skill`: optional minimum effective skill (`calculate_skill_with_traits`); pair with `required_building_worker_skill`, or omit skill to use the building type’s `skill_name` from `building_types_json`.

Removed: `required_building_traits` (building instances do not carry `traits` in this project; the key is ignored if present in old JSON).
