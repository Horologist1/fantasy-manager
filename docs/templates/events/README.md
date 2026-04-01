# Event templates

- Main template: `event.template.json` (full event). Per-choice fragment: `event_choice.template.json`.
- Schema reference: `docs/json_schema_canonical.md` and `game/data/json_schema_standard.md`.
- Authoring guide: `docs/json_modding_guide.md` (§4 recipe for events).

## Choice-level traits

- **Prefer `required_traits`** (list). For a single trait, use e.g. `"required_traits": ["Magical"]`.
- **`required_trait`** (single string) is **legacy**; the game merges it into `required_traits` at runtime. New content should leave `required_trait` as `null` and use `required_traits` only.
- **`excluded_traits`**: worker must not have any of these traits.
- **`trait_visibility`**: `hide` omits the option if traits fail; `blocked` shows it locked (use `blocked_message`).

## Choice-level effect worker filter

- **`restrict_worker_effects_to_filter`**: when `true` with a non-empty **`effect_worker_filter`**, worker-targeted outcome keys (`add_trait` resolution, `skill_modifiers`, health/energy on the acting worker, `joy`) only apply if the worker matches the filter. Global rewards/penalties (`money`, `reputation`, `event_flags`, `custom`, …) are not gated.
- **`effect_worker_filter`**: profession lists (`required_active_professions`, `forbidden_active_professions`), traits (`required_traits`, `excluded_traits`), optional min skill (`min_skill` or `required_building_worker_min_skill` plus skill name or building default). See `brothel_worker_caution` in `events_building.json` for `forbidden_active_professions: ["manager"]` with pregnancy risk.
- **`message_failure_worker_effect_skipped`**: optional alternate `message_failure` when a filtered failure applies money/reputation but skips the worker trait outcome.

## Manager gender (Lord / Lady)

- **`player_gender_requirement`** (event root, optional): restricts the event to managers whose canonical gender matches. Used when building the random event pool (`select_possible_events`), **not** per choice.
- **Runtime rule:** if `player_title` is `"lord"` (case-insensitive, trimmed), the manager is **`"male"`**; otherwise (e.g. Lady) **`"female"`**.
- **JSON values:** `male`, `female`, or aliases `lord`, `lady` (normalized to male/female before comparison). Omit the key or use `null` for no restriction.
- **Daily stories** use the same key and semantics on each story object (see `docs/templates/buildings/daily_story.template.json`).
- **Interactions** use **`gender_filter`** on the interaction object with the same value set; see `docs/templates/interactions/README.md`.
- **`worker_gender_requirement` on the event object** is listed in templates for historical/schema completeness but is **not** applied by the random/building event filter. Use **`worker_gender_requirement` on daily stories** or **`worker_gender` on interactions** for worker-side filtering. `devkit/validate_event_mechanics.py` emits a warning if this key is set on an event.

## Choice level

- Random events have **no** `player_gender_requirement` / gender fields on individual **choices**; gate at the event root only (`event_choice.template.json`).
