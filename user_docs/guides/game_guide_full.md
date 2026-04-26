# Fantasy Manager - Full Game Guide

This guide documents the current game loop, management systems, progression gates, and common troubleshooting paths.

## 1) Core Daily Loop

1. Open tavern hub.
2. Review workers/buildings/inventory.
3. Assign jobs and adjust comfort.
4. Use interactions/training/shopping as needed.
5. Press **Next Day**.
6. Review daily report (income, costs, outcomes, images/loot).
7. Repeat with adjustments.

Primary loop entry:
- `game/scripts/core/screens.rpy` (`screen tavern`, `Next Day` button)
- `game/scripts/main_flow.rpy` (`label next_day`)
- `game/scripts/events/event_daily_exec.rpy` (`process_next_day`, `process_daily_events`)

## 2) Main Screens and What They Do

## Tavern (Hub)
- Central command screen for daily decisions.
- Quick access to map, buildings, workers, storage, and next day.

## City Map
- Recruiting, building purchases, shops, progression locations.
- Some systems unlock over time or through objectives.

## Manage Buildings
- Assign workers by profession/job.
- Upgrade buildings (cost curve by level).
- Configure building skill bonus and pay its upkeep.

## Manage Workers
- Reassign, rest, quick recovery actions.
- Filter by building and job.
- Open worker detail panel for deeper control.

## Worker Details
- Comfort, relationship, automation, equipment, interactions.
- Stats and trait effects are applied at daily resolution.
- Interactions can be filtered by `required_traits` and `excluded_traits`.

## Storage / Trading
- Move items between manager and workers.
- Equip/unequip and use consumables.
- Shop mode uses similar panel logic for buy/sell flows.

## Daily Report
- Shows each processed outcome row with earnings/result.
- Totals are aggregated from report rows and building costs.

## 3) Economy Model (Practical)

## Income
- Comes from per-worker story outcomes in `daily_report`.
- Each row has `earnings` based on profession story formulas and modifiers.

## Costs
- Building base maintenance.
- Worker comfort/upkeep costs.
- Building skill bonus upkeep.
- Optional system costs (academy entries, etc.).

### Building level scaling (assigned workers)

Daily charges for **assigned** workers in a building include:

1. **Comfort:** sum of `(worker comfort level) × (difficulty comfort multiplier)`, then multiplied by a **building-level factor**:
   - `1 + 0.034 × (level − 1)^1.68`
   - Approximate values by building level 1–5: **1.00 / 1.03 / 1.11 / 1.22 / 1.33**
2. **Upkeep:** sum of per-worker upkeep (`5 + worker level` for bought workers, `20 + 3 × worker level` for recruited), then multiplied by:
   - `1 + 0.052 × (level − 1)^1.68`
   - Approximate values by building level 1–5: **1.00 / 1.05 / 1.17 / 1.33 / 1.51**

**Story** difficulty already uses a higher comfort multiplier per worker; only part of the **extra** comfort scaling from building level is applied there, so early game does not double-punish comfort.

Base maintenance (`base_per_level × building level`) is unchanged by these formulas; see `game/scripts/events/event_daily_exec.rpy` (`compute_worker_portion_daily_costs`, `process_next_day`).

## Net Result
- Calculated after all worker/event processing.
- Report and backend economy are expected to match by design.

## 4) Workers, Stats and Traits

## Worker Assignment
- Jobs are profession IDs inside each building type.
- Daily processing uses a unified profession loop (including `rest` and special-building professions).

## Core Daily Resolution
- Regeneration and daily effects run at day start.
- Stories are selected per profession and resolved by roll/skill.
- Consequences mutate worker stats and relationship values.

## Traits
- Traits modify skills, earnings, caps/minimums, and daily effects.
- Some traits are also used for image selection prefixes.

## 5) Buildings, Professions and Daily Stories

Data source:
- `game/data/buildings/building_types.json`

Structure:
- Building types contain professions.
- Professions contain `daily_stories`.
- Stories define formulas, descriptions, consequences, and optional loot.

Filters now supported in stories:
- `worker_gender_requirement`
- `required_traits`
- `excluded_traits`
- `stat_requirements`

Compatibility behavior:
- If filtering leaves no compatible stories, resolver can fallback to legacy-compatible pool for stability.

## 6) Random Events and Seasonal Events

Data source:
- `game/data/events/events_building.json`
- `game/data/events/events_seasonal.json`

Pipeline:
- Load candidate events.
- Apply flag/building/cooldown/condition filters.
- Run choice flow and apply effects.
- Choice options can be trait-gated (`required_traits` / `excluded_traits`) and either hidden or shown as locked. The older single-field `required_trait` is still supported but treated as legacy; authors should prefer `required_traits` (see `docs/json_schema_canonical.md`).

New event availability gates:
- `requires_assigned_worker`: event appears only if a matching owned building has at least one assigned worker.
- `required_building_worker_traits`: event appears only if a worker in a matching owned building has all listed traits.
- `required_active_professions` / `forbidden_active_professions`: gate on `servant_jobs` profession ids (active = not `rest`/`unassigned`).
- `required_building_worker_min_skill` (+ optional `required_building_worker_skill`): min effective skill among assigned workers in that building.

Worker-aware visuals:
- When a worker is selected for an event path, media resolution can prioritize worker folders.

## 7) Image and Media Behavior (Player-Level)

- Daily outcome visuals and event visuals can use worker-specific files.
- If no specific file is found, system falls back to broader paths.
- Both image and video extensions are supported in media lookup.

Detailed technical rules:
- See `docs/image_selection_guide.md`.

## 8) SFW / NSFW Behavior

- NSFW toggle controls content visibility and processing paths.
- In SFW mode, libido-based penalties are disabled at runtime.
- JSON schema can still include libido keys for standardization.

## 9) Progression Systems

## Recruiting
- Event-based and market-like flows exist.
- Limited by day and internal caps.
- Procedural recruit candidates default to `comfort_desired = 4`.
- If a recruit offer applies a wage discount (`cost_modifier < 1.0`), entry comfort is set to one point below desired (typically `3` for those procedural recruits).

## Academy / Training
- Academy training jobs (`academy_*`) run through the same profession pipeline as other jobs, with deterministic/no-roll resolution.
- Recommended data shape for stable economics is one story per worker/day (`daily_story_count.base = 1`, `bonus_formula = "0"`).

## Arena / Combat and Quests
- Long-term progression loops, unlocks and gated systems.
- Some quest systems and story routes have flag-gated transitions.

## Relationship Routes
- VN-like branches (for example Yvara route) track route stats and day-gated actions.

## 10) Save/Load and Stability Notes

- Calendar and many systems use store/default vars that persist with saves.
- Event flags/occurrence/cooldowns are tracked in store dictionaries.
- Large JSON edits should be validated for parse correctness before runtime.

## 11) Troubleshooting

## Daily report looks wrong
- Check row-level `earnings` and building cost components.
- Confirm there is no duplicate post-processing step changing money totals.

## No event appears
- Verify cooldowns, required/excluded flags, and `conditions.start_when/stop_when`.
- Confirm matching building types are owned and active.

## Images not appearing
- Verify filenames, prefixes, and extension support.
- Check worker folder and fallback folder content.
- See `docs/image_selection_guide.md`.

## JSON changes break loading
- Validate syntax and required structure for target type.
- Compare with templates in `docs/templates/`.
- Use canonical definitions in `docs/json_schema_canonical.md`.

## 12) Recommended Workflow for Big Content Edits

1. Copy template from `docs/templates/`.
2. Fill IDs/text/formulas incrementally.
3. Keep all schema keys present (neutral defaults where not used).
4. Validate JSON parse.
5. Run a short in-game smoke test:
   - one day cycle
   - one event flow
   - one interaction flow
   - one report inspection
