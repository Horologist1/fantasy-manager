# Building templates (professions & daily stories)

Copy `profession.template.json` / `daily_story.template.json` / `daily_story_extension.template.json` into your mod data. Runtime merges `daily_story_extensions` by `building_id` + `profession_id`.

Special buildings note:
- `Academy` and `Arena` professions are authored in `game/data/buildings/special_buildings.json`.

## Profession: staffing (money)

Optional keys on each **profession**. **Runtime** treats a missing key as multiplier **1.0** for that branch. **Manager UI** only shows staffing hints if at least one of `staffing_penalty` / `staffing_bonus` is present on the profession JSON (see main `building_types.json` for patterns):

| Key | Meaning |
|-----|--------|
| `staffing_penalty` | Earnings multiplier for this **job** when **0** workers are assigned to it (e.g. `0.5`). |
| `staffing_bonus` | Earnings multiplier when **≥1** worker is in this job (often `1.0`; use `>1` only if staffed should boost revenue). |

Per building day: the game multiplies **all** non-`rest` professions’ factors (empty vs staffed), then **clamps** the product to **[1/3, 3]**. That factor applies to each daily story’s evaluated **earnings** for workers in **that building only**.

## Profession: synergy (d100 skill check)

| Key | Meaning |
|-----|--------|
| `presence_roll_bonus` | **Optional.** Integer **per worker** in this job. Summed across professions as `bonus × worker_count`, then **clamped to [−40, 40]** for the whole building. Added to the **skill threshold** (roll-under d100: success if `die ≤ threshold`). **Positive** helps; **negative** hurts. **Omit** the key (or use `0`) if this role should not show or apply synergy. |

Synergy is computed **per owned building** from that building’s `servant_jobs` counts; it does not leak across buildings.

## Daily story: manager and worker gender

- **`worker_gender_requirement`**: optional; must match the assigned worker’s `gender` string.
- **`player_gender_requirement`**: optional; same semantics as random events (`male`/`female`/`lord`/`lady`; Lord title → male). If no story matches after filtering, the runtime relaxes this gate (then eligibility), same pattern as legacy worker-only fallback.

## Daily story: check & earnings formulas

- **Skill threshold** (before clamp to 0–100): averaged `skill_options` skill (with difficulty/libido penalties) + `difficulty_modifier` + weighted `positive_traits` / `negative_traits` + **building synergy** above. The **die** is uniform 1–100; synergy does **not** add to the die.
- **`earnings`** strings are evaluated with `skill`, `level`, and **`roll`** (the natural d100 roll). Building staffing money multiplier is applied **after** that evaluation.

## Deterministic professions (`rest`, `academy_*`)

- Runtime processes `rest` and `academy_*` via the same profession loop, but they are handled as **deterministic/no-roll** branches.
- For these jobs, author stories around:
  - `description` (and optional `descriptions.success` fallback)
  - `consequences.success`
- Recommended JSON for one session per worker/day (especially Academy training):
  - `daily_story_count: { "base": 1, "bonus_formula": "0" }`
- Keep `daily_story_count` explicit in data so behavior stays stable if formulas or reputation tuning changes elsewhere.

## Files

- `building.sample.json` — minimal full building type + one profession + one story.
- `daily_story_trait_roll_example.json` — trait dict weights on stories.
