# Worker Template

Use `worker.template.json` as the base for new workers. Add entries to the appropriate file in `game/data/workers/`:

- **workers_sfw_unique.json** – SFW, unique (flower names, recruit list)
- **workers_sfw_other.json** – SFW, non-unique
- **workers_nsfw_unique.json** – NSFW, unique
- **workers_nsfw_other.json** – NSFW, non-unique

## Required fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Display name (unique across workers) |
| `folder` | string | Image folder under `images/workers/<folder>/`. Must match folder name exactly |
| `cost` | number | Purchase/recruit cost |
| `nsfw` | boolean | Only shown when NSFW mode is enabled |
| `unique` | boolean | `true` = flower-themed names, single instance; `false` = procedural names, can appear multiple times |
| `encounter_only` | boolean | `true` = eligible for recruitment encounter pool (`Recruit workers`), `false` = market/buy pool behavior |
| `monster` | boolean | `true` = monster worker (encounter_only, nsfw defaults) |
| `procedural` | boolean | Usually `false` |
| `skills` | object | All 21 skills, each 0–100. See template |
| `names_list` | string | Key from `data/names.json`: `western_male`, `western_female`, `fantasy_male`, `fantasy_female`, `eastern_male`, `eastern_female`, `monster_male`, `monster_female` |
| `traits` | array | Trait names from `data/traits/` (e.g. `"Human"`, `"Orc"`, `"Goblin"`, `"Elf"`, `"Demon"`) |
| `description` | string | Shown in recruit/worker details |
| `gender` | string | `"male"` or `"female"`. Affects image fallback (`guy` vs `blossom`) |
| `comfort_desired` | number | Base comfort preference (1–5) |

## Optional fields

| Field | Type | Description |
|-------|------|-------------|
| `images_folder` | string | Override for image folder if different from `folder` |
| `recruit_only` | boolean | If set, worker only appears in recruit list, not encounters |

## Comfort defaults by acquisition path

- **Buy Servants** normalizes market workers to `comfort_desired = 1`.
- **Procedural Recruit Workers** currently default to `comfort_desired = 4`.
- Recruitment options with discounted wage (`cost_modifier < 1.0`) start at one comfort point below desired (typically `3` for procedural recruits).

## Image folder requirements

Worker images must live in `game/images/workers/<folder>/`. See `docs/image_selection_guide.md` for required images:

- `profile`, `rest`
- Skills: `agility`, `combat`, `craft`, `clever`, `charm`, `service` (+ `*_failure`)
- `strip` / `striptease` (+ failure)
- `sex`, `oral`, `anal`, `hand`, `extreme`/`beast`, `group`, `homo`/`gay`, `bdsm`, `special` (+ failure)
- `obedience`, `romance_lord`, `romance_lady`, `friendship` (legacy aliases `romance_male`/`romance_female` are still supported)
- Discipline, friendship, romance interaction chain images
