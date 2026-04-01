# JSON Standard (Modding)

This project uses explicit, copy-friendly JSON templates. Entries now include all known keys for their type, even when some keys are neutral.

Default neutral values:
- `null` for optional text/ids
- `[]` for list fields
- `{}` for object maps
- `0` for numeric fields
- `false` for booleans

## Event Schema

### Event keys
- `id`, `description`, `weight`, `limited`, `max_occurrences`, `cooldown_days`
- `event_probability`, `guaranteed`
- `worker_selection`
- `worker_gender_requirement` — **ignored** by random/building event pool; use daily story / interaction fields for worker gender. Validator warns if set.
- `player_gender_requirement` — optional `male`/`female`/`lord`/`lady`; Lord title → male, else female; filters `select_possible_events`.
- `requires_assigned_worker`, `required_building_worker_traits`
- `required_active_professions`, `forbidden_active_professions` (profession ids from `servant_jobs`, not `rest`/`unassigned`)
- `required_building_worker_min_skill`, `required_building_worker_skill` (optional min effective skill in building; skill name defaults from building type)
- `building_type`
- `background_image`, `success_image`, `failure_image`
- `nsfw`
- `required_flags`, `excluded_flags`
- `conditions` (`start_when`, `stop_when`)
- `choices`
- compatibility fields: `start_when`, `stop_when`

### Choice keys
- `option`, `condition`, `threshold`
- `required_traits`, `excluded_traits` — **recommended** for trait gating (worker must have all required, none excluded). Use a one-element list for a single trait.
- `required_trait` — **legacy**; same as appending one string to `required_traits`. Prefer `required_traits` in new JSON.
- `trait_visibility` (`hide` or `blocked`), `blocked_message`
- `message`, `message_success`, `message_failure`
- `message_failure_worker_effect_skipped` (optional): alternate failure narrative when worker-scoped effects are skipped under `restrict_worker_effects_to_filter` (see canonical doc).
- `restrict_worker_effects_to_filter` (bool), `effect_worker_filter` (object) — optional gate so trait/skill/health/energy outcomes apply only to workers matching profession/trait/skill rules; money/reputation and other global effect keys are unchanged.
- `conditions`, `required_flags`, `excluded_flags`
- `effect`

### Effect keys
- Flat: `money`, `reputation`, `custom`, `event_flags`, `item_id`, `loot_rolls`, `worker_name`, `random_worker`, `add_trait`, `skill_modifiers`
- Branched: `success`, `failure` (same shape as flat payload where applicable)
- `success_chance` (0.0–1.0, optional): only affects **no-condition** choices that use the probability branch; **ignored** on skill / `building_skill` choices. See canonical doc.
- `add_trait`: `name`, `duration`, `target`
- `skill_modifiers`: `{ "SkillName": delta }` — modifies worker base skill (e.g. Charm +3). Requires worker context.

## Interaction Schema

Top-level keys:
- `id`, `name`, `description`
- `interaction_level`, `interaction_type`
- `cost_energy`, `cost_money`
- `effect`
- `gender_filter` (manager): optional; `male`/`female`/`lord`/`lady`, same normalization as event `player_gender_requirement`
- `worker_gender`
- `categories`, `image`, `nsfw`
- `stat_requirements`
- `specific_workers`, `required_traits`
- `excluded_traits`
- `required_flags`, `excluded_flags`

`effect` keys:
- `romance`, `relationship`, `joy`, `rebelliousness`, `libido`, `flags`
- `add_trait`: string (trait name) or `{ "name": "...", "duration": 0 }` — adds trait to worker
- `remove_trait`: string (trait name) or `{ "name": "..." }` — removes trait from worker
- `flags.<flag_name>` uses `{ "value": false, "duration": 0 }`

Trait filters:
- `required_traits`: worker must have all listed traits
- `excluded_traits`: worker must have none of the listed traits

## Building / Profession / Daily Story Schema

### Building type keys
- `id`, `name`, `skill_name`, `skill_description`
- `nsfw`, `allowed_map_locations`, `professions`

**Runtime economy (not in JSON):** each day, assigned workers incur comfort and upkeep charges that also scale with the **instance** `base_level` of that building: upkeep total × `1 + 0.052×(L−1)^1.68`, comfort total × `1 + 0.034×(L−1)^1.68` (Story difficulty blends down the comfort-level extra). See `docs/game_guide_full.md` (Economy → Building level scaling).

### Profession keys
- `id`, `name`, `description`, `nsfw`, `difficulty`
- `skills`, `max_daily_workers`
- `staffing_penalty` (optional float): money mult when **0** workers in this job
- `staffing_bonus` (optional float): money mult when **≥1** worker in this job
- `presence_roll_bonus` (optional int): per worker; summed per building into d100 **threshold** change (± cap); omit/`0` if unused
- `daily_story_count` (`base`, `bonus_formula`)
- `daily_stories`
- deterministic/no-roll convention: for `rest` and `academy_*`, keep `daily_story_count` explicit (recommended `{ "base": 1, "bonus_formula": "0" }`) when you want one processing pass per worker/day.

### Daily story keys
- `id`, `weight`, `report`, `description`
- `difficulty_modifier`, `worker_gender_requirement`, `player_gender_requirement` (optional; same semantics as events), `nsfw_only`
- `skill_options`, `event_image_skill_exclude`
- `positive_traits` (dict: trait → weight; **threshold** bonus + message pick weight), `negative_traits` (dict: trait → weight)
- trait message keys: `trait_msg_success`, `trait_msg_failure`, `trait_success` (legacy fallback)
- `required_traits`, `excluded_traits`, `stat_requirements`
- `descriptions` (`failure`, `mediocre`, `success`, `critical_success`)
- `earnings` (`failure`, `mediocre`, `success`, `critical_success`) — env: `skill`, `level`, `roll` (d100)
- `consequences` (`failure`, `mediocre`, `success`, `critical_success`)
- consequence keys: `energy`, `health`, `joy`, `rebelliousness`, `romance`, `relationship`, `reputation`, `libido`, `obedience`
- consequence trait/item keys: `trait_chance` (array of `{ "trait": "Name", "chance_percent": 1-100, "duration"?: days }`; use `chance_percent: 100` for a guaranteed grant; alias keys `name` / `percent` accepted like training), `trait_remove_chance` (same entry shape without `duration`; chance roll removes trait if worker has it), `give_item` (item_id string or `{ "item_id": "...", "quantity": 1 }`)
- `story_image`, `failure_image`
- `loot` (`rolls`, `bonus_items`, `monster_worker`, `captured_worker`)
- deterministic/no-roll usage (`rest`, `academy_*`): runtime uses `description` (or `descriptions.success` fallback) plus `consequences.success`; roll-dependent branches are optional for compatibility.

## Items Schema

Top-level:
- `items`, `excluded_from_shops`

Item keys:
- `id`, `name`, `display_name`, `type`
- `effect`
- `description`, `durability`, `price`, `weight`, `nsfw`

`effect` keys:
- `custom`, `skill_modifiers`, `attribute_modifiers`, `daily_effects`

## Traits Schema

Trait keys:
- `name`, `conflicts`, `removes_traits`
- `modifiers`
- `description`, `nsfw`

`modifiers` canonical keys:
- `skill_modifiers`, `attribute_caps`, `attribute_minimums`, `daily_effects`
- `earnings_multiplier`, `libido_max`, `libido_regeneration`
