# JSON Modding Guide

This guide describes how to create and modify content JSON safely using the canonical schema.

## 1) Source of truth

- Canonical schema: `docs/json_schema_canonical.md`
- Practical schema summary: `game/data/json_schema_standard.md`
- Templates:
  - `docs/templates/events/`
  - `docs/templates/interactions/`
  - `docs/templates/buildings/`
  - `docs/templates/items/`
  - `docs/templates/traits/`
  - `docs/templates/workers/`

## 2) Standardization rule

Every entry should include all keys for its type, even if some keys are neutral:
- `null`, `[]`, `{}`, `0`, `false`

Exception for runtime readability:
- Do not enumerate every possible flag in `required_flags`, `excluded_flags`, or `effect.flags`.
- Keep only flags that are actually used by that interaction/event.

Benefits:
- easy copy/modify/replicate
- fewer missing-field bugs
- consistent review and tooling

## 3) Safe editing workflow

1. Copy template file from `docs/templates/`.
2. Paste as a new entry in target `game/data/...` file.
3. Replace only required fields first (`id`, `name`, text, formulas).
4. Keep unused keys with neutral defaults.
5. Validate JSON parse before launching game.
6. Test one focused scenario in-game.

## 4) Recipe: Create a new event

1. Start from `docs/templates/events/event.template.json`.
2. Set:
   - `id`, `description`, `choices`
   - `building_type` and `worker_selection` as needed
3. If outcome-specific logic exists:
   - use `choices[].effect.success` and `choices[].effect.failure`
4. If condition gating is needed:
   - set `conditions.start_when` / `conditions.stop_when`
   - optional `required_flags` / `excluded_flags`
   - optional trait gating at choice level:
     - `required_trait` (single, legacy-compatible)
     - `required_traits` (list)
     - `excluded_traits` (list)
     - `trait_visibility`: `hide` or `blocked`
     - `blocked_message` for locked option text
   - optional worker/building gates:
     - `requires_assigned_worker`
     - `required_building_worker_traits`
     - `required_building_traits`
   - optional `player_gender_requirement`: `"male"` (Lord only) or `"female"` (Lady only); `null` = both
5. Add image keys:
   - `background_image`, `success_image`, `failure_image`

Behavior notes:
- If trait requirements fail and `trait_visibility` is `hide`, option is not shown.
- If trait requirements fail and `trait_visibility` is `blocked`, option is shown as locked.

## 5) Recipe: Create interaction with prerequisites

1. Start from `docs/templates/interactions/interaction.template.json`.
2. Set base metadata: `id`, `name`, `description`, `categories`, `image`.
3. Configure costs and effects.
   - Use `effect.libido` explicitly for interactions that should consume or grant libido.
   - Keep those interactions `nsfw: true` when they are sexual in nature.
   - Use `effect.add_trait` (string or `{ "name": "...", "duration": 0 }`) to add a trait to the worker.
   - Use `effect.remove_trait` (string or `{ "name": "..." }`) to remove a trait from the worker.
4. Add prerequisites:
   - `stat_requirements`
   - `required_traits`
   - `excluded_traits`
   - `specific_workers`
   - `required_flags` and `excluded_flags`
5. Keep flag structure explicit for readability.

## 6) Recipe: Create daily story with trait/stat filters

1. Start from `docs/templates/buildings/daily_story.template.json`.
2. Fill:
   - `id`, `report`, `descriptions`, `earnings`, `consequences`
3. Use consequence keys for trait/item rewards (per outcome: failure, mediocre, success, critical_success):
   - `add_trait`: string (trait name) or `{ "name": "...", "duration": 0 }` — adds trait to the worker.
   - `give_item`: item_id string or `{ "item_id": "...", "quantity": 1 }` — gives item(s) to manager inventory.
4. Add filters:
   - `required_traits`
   - `excluded_traits`
   - `stat_requirements`
   - optional `worker_gender_requirement`
   - optional `nsfw_only` to show that story only when NSFW mode is enabled
5. Add trait specialization (optional): `positive_traits` — dict {trait: weight}. `negative_traits` — dict {trait: weight}. Weight = roll modifier + message pick probability. Use `trait_msg_success` and `trait_msg_failure` templates.
6. Add `story_image` / `failure_image` and optional `loot`.

See `docs/templates/buildings/daily_story_trait_roll_example.json` for a full example of trait specialization.

## 7) Recipe: Create event chain for a specific worker

1. Use `worker_name` to pin the event to a worker (e.g. `"worker_name": "Aelis"`).
2. Use `worker_selection`: `"random"` so the pre-selected worker is used for skill checks.
3. Use `building_type` to restrict to buildings where the worker is assigned.
4. Use `conditions.start_when`: `"has_worker:WorkerName"` so the event only appears when that worker exists.
5. Chain events with flags:
   - Event 1: `effect.event_flags`: `{ "event_1_done": true }`, `excluded_flags`: `{ "event_1_done": true }` (so it does not repeat).
   - Event 2: `required_flags`: `{ "event_1_done": true }`, `excluded_flags`: `{ "event_2_done": true }`, `effect.event_flags`: `{ "event_2_done": true }`.
6. For skill rewards (e.g. Charm), add `skill_modifiers` to effects. See `docs/EVENT_SKILL_MODIFIERS_NEEDED.md` for required code changes.

See `game/data/events/events_aelis_chain.json` for a full 5-event chain example.

## 8) Recipe: Create a new worker

1. Start from `docs/templates/workers/worker.template.json`.
2. Set required fields:
   - `name`, `folder` (must match `images/workers/<folder>/`), `cost`, `gender`
   - `names_list` from `data/names.json` (e.g. `western_male`, `fantasy_female`, `monster_male`)
   - `traits` from `data/traits/` (e.g. `["Human"]`, `["Orc"]`, `["Goblin"]`)
   - `description`
3. Choose file:
   - `workers_nsfw_other.json` for NSFW encounter-only monsters (e.g. Amanita, Moss)
   - `workers_nsfw_unique.json` for NSFW unique workers (Aspen, Violet, etc.)
   - SFW variants for non-NSFW workers
4. For monster workers: `monster: true`, `encounter_only: true`, `unique: false`, `nsfw: true`.
5. Adjust `skills` (0–100). Trait modifiers from `traits_races.json` apply at runtime.
6. Create image folder `game/images/workers/<folder>/` with required images (see `docs/templates/workers/README.md` and `docs/image_selection_guide.md`).

## 9) SFW compatibility rules

Keep libido fields in schema for consistency, but in SFW mode:
- libido effects should be inactive at runtime
- content that depends on NSFW should use `nsfw` flags and runtime toggles

Practical guidance:
- do not rely on libido penalties for core SFW balancing
- keep SFW-friendly fallback outcomes/messages

## 10) Common mistakes to avoid

- Removing required structural keys for the entity type.
- Expanding all possible flags in every interaction (high noise, low value).
- Mixing object and non-object types for the same key.
- Using missing outcome branches in `earnings`/`descriptions`.
- Forgetting flag keys in one file while using them in another.
- Putting templates inside runtime data folders.

## 11) Validation checklist before commit

- JSON parses successfully.
- New IDs are unique.
- Required branches (`failure/mediocre/success/critical_success`) exist where expected.
- Images follow naming/folder conventions.
- SFW mode still behaves correctly.
