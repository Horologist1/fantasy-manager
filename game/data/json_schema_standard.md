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
- `worker_selection`, `worker_gender_requirement`, `player_gender_requirement`
- `requires_assigned_worker`, `required_building_worker_traits`, `required_building_traits`
- `building_type`
- `background_image`, `success_image`, `failure_image`
- `nsfw`
- `required_flags`, `excluded_flags`
- `conditions` (`start_when`, `stop_when`)
- `choices`
- compatibility fields: `start_when`, `stop_when`

### Choice keys
- `option`, `condition`, `threshold`
- `required_trait`, `required_traits`, `excluded_traits`
- `trait_visibility` (`hide` or `blocked`), `blocked_message`
- `message`, `message_success`, `message_failure`
- `conditions`, `required_flags`, `excluded_flags`
- `effect`

### Effect keys
- Flat: `money`, `reputation`, `custom`, `event_flags`, `item_id`, `loot_rolls`, `worker_name`, `random_worker`, `add_trait`, `skill_modifiers`
- Branched: `success`, `failure` (same shape as flat payload where applicable)
- `add_trait`: `name`, `duration`, `target`
- `skill_modifiers`: `{ "SkillName": delta }` — modifies worker base skill (e.g. Charm +3). Requires worker context.

## Interaction Schema

Top-level keys:
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

### Profession keys
- `id`, `name`, `description`, `nsfw`, `difficulty`
- `skills`, `max_daily_workers`
- `daily_story_count` (`base`, `bonus_formula`)
- `daily_stories`

### Daily story keys
- `id`, `weight`, `report`, `description`
- `difficulty_modifier`, `worker_gender_requirement`
- `skill_options`, `positive_traits` (dict: trait → weight; roll bonus + message pick weight), `negative_traits` (dict: trait → weight)
- trait message keys: `trait_msg_success`, `trait_msg_failure`, `trait_success` (legacy fallback)
- `required_traits`, `excluded_traits`, `stat_requirements`
- `descriptions` (`failure`, `mediocre`, `success`, `critical_success`)
- `earnings` (`failure`, `mediocre`, `success`, `critical_success`)
- `consequences` (`failure`, `mediocre`, `success`, `critical_success`)
- consequence keys: `energy`, `health`, `joy`, `rebelliousness`, `romance`, `relationship`, `reputation`, `libido`, `obedience`
- consequence trait/item keys: `add_trait` (string or `{ "name": "...", "duration": 0 }`), `give_item` (item_id string or `{ "item_id": "...", "quantity": 1 }`)
- `story_image`, `failure_image`
- `loot` (`rolls`, `bonus_items`, `monster_worker`, `captured_worker`)

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
