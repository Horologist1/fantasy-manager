# Fantasy Manager Field Guide

Player and modder guide: how the game works, its formulas, and every image name the
game looks for. Published next to the devkit:

- Online: https://horologist1.github.io/fantasy-manager/guide/ (`#play`, `#ref`, `#img` open a tab)
- Offline copy shipped with the game: `user_docs/guides/field_guide.html`

## Files

| File | What it is | Updated by |
|---|---|---|
| `part_play.html` | "How to play" tab: loop, workers, buildings, jobs, traits, items, interactions, events | Hand |
| `part_ref.html` | "Formulas & data" tab: formulas, data files, JSON fields, changes from old guides | Hand |
| `part_img.html` | "Images & modding" tab: lookup rules and fallback chain | Hand |
| `template.html` | Page shell, styles and the script that renders the image lists | Hand |
| `build_field_guide.py` | Reads `game/data/` and builds the page | Runs automatically |

## Updating with the game

- **Generated lists** are rebuilt from `game/data/` every time: image names (stories,
  events, interactions, training), the full **trait list** (from `data/traits/`) and
  **how to get each worker** (from `data/workers/` and `data/events/recruit/`).
  Two hand-kept tables in `build_field_guide.py` cover what the data can't tell:
  `WORKER_NOTES` / `LANISTA_NOTE` (workers that join through a story: Yvara, the
  Lanista, Kar and Kara) and `NEVER_GRANTED` (traits defined but given by nothing).
  Update them when those rules change.
- The **Goals and milestones** chapter (objectives, ending rewards, Manager Level
  sources, places to unlock) is hand-written in `part_play.html`.
- Image lists (stories, events, interactions, training) are rebuilt from `game/data/`
  every time. Nothing to do: the Pages workflow regenerates the online guide on every
  push that touches game data or the devkit.
- **Mechanics and formulas** are written by hand. When a release changes a rule (costs,
  roll math, caps, new building, new system), edit `part_play.html` and/or `part_ref.html`
  and bump the version in `template.html` ("Checked against the code of version …").
  The values were verified against these code locations (0.9.6.2t1):
  - job roll, earnings, daily loop, costs: `game/scripts/events/event_daily_exec.rpy`
  - stats, regen, earnings caps: `game/scripts/workers/worker_stats.rpy`
  - leveling, skill uses, difficulty, upgrades: `game/scripts/script.rpy`
  - reputation, building logic: `game/scripts/buildings/building_logic.rpy`
  - interactions: `game/scripts/workers/worker_interactions.rpy`, `core/screens.rpy`
  - events and managers: `python-packages/fm_events/`, `scripts/events/`
- **Image lookup rules**: if `get_skill_search_patterns` or the fallback order in
  `game/scripts/events/event_visuals.rpy` changes, update `SKILL_FILES` in
  `build_field_guide.py` and the rules in `part_img.html`.

## Building locally

```
cd devkit_web
npm run guide      # writes user_docs/guides/field_guide.html
npm run check      # bake + docs + guide + tests + offline build
```
