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
- `worker_selection`, `worker_gender_requirement`, `player_gender_requirement`
- `requires_assigned_worker`
- `required_building_worker_traits`
- `required_building_traits`
- `building_type`
- `background_image`, `success_image`, `failure_image`
- `nsfw`
- `required_flags`, `excluded_flags`
- `conditions.start_when`, `conditions.stop_when`
- `choices`
- compatibility keys: `start_when`, `stop_when`

### Event choice object
- `option`, `condition`, `threshold`
- `required_trait`, `required_traits`, `excluded_traits`
- `trait_visibility` (`hide` or `blocked`)
- `blocked_message`
- `message`, `message_success`, `message_failure`
- `conditions.start_when`, `conditions.stop_when`
- `required_flags`, `excluded_flags`
- `effect`

### Event effect object
- Flat keys: `money`, `reputation`, `custom`, `event_flags`, `item_id`, `loot_rolls`, `worker_name`, `random_worker`, `add_trait`
- Branch keys: `success`, `failure`
- `add_trait`: `name`, `duration`, `target`

## Interactions

### Interaction object
- `id`, `name`, `description`
- `interaction_level`, `interaction_type`
- `cost_energy`, `cost_money`
- `effect`
- `gender_filter`, `worker_gender`
- `categories`, `image`, `nsfw`
- `stat_requirements`
- `specific_workers`, `required_traits`
- `excluded_traits`
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
- `daily_story_count.base`, `daily_story_count.bonus_formula`
- `daily_stories`

### Daily story object
- `id`, `weight`, `report`, `description`
- `difficulty_modifier`
- `worker_gender_requirement`
- `skill_options`, `relevant_traits`, `trait_success`
- `required_traits`, `excluded_traits`, `stat_requirements`
- `descriptions.failure`, `descriptions.mediocre`, `descriptions.success`, `descriptions.critical_success`
- `earnings.failure`, `earnings.mediocre`, `earnings.success`, `earnings.critical_success`
- `consequences.failure|mediocre|success|critical_success`
- consequence stat keys: `energy`, `health`, `joy`, `rebelliousness`, `romance`, `relationship`, `reputation`, `libido`, `obedience`
- consequence trait/item keys: `add_trait` (string or `{ "name": "...", "duration": 0 }`), `give_item` (item_id string or `{ "item_id": "...", "quantity": 1 }`)
- `story_image`, `failure_image`
- `loot.rolls`, `loot.bonus_items`, `loot.monster_worker`, `loot.captured_worker`

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

## New Filtering Notes

- Event availability can now be gated by:
  - `requires_assigned_worker`: event only appears if at least one assigned worker exists in a matching owned building.
  - `required_building_worker_traits`: event only appears if a worker in a matching owned building has all listed traits.
  - `required_building_traits`: event only appears if the matching owned building has all listed traits/tags in `building["traits"]`.
- Interaction trait filtering now supports both:
  - `required_traits` (worker must contain all)
  - `excluded_traits` (worker must contain none)
