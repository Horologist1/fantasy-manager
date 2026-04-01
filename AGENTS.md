# AGENTS.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project type
- This is a **Ren'Py game project** with a data-driven content model:
  - Runtime code in `game/scripts/**/*.rpy`
  - Game content in `game/data/**/*.json`
  - Editor/automation tooling in `devkit/` and `tools/`

## Common commands

### Run validators / content checks
- Validate event mechanics (default event files):
  - `python devkit/validate_event_mechanics.py`
- Validate a single event file:
  - `python devkit/validate_event_mechanics.py --files game/data/events/events_common.json`

### Run data maintenance scripts
- Normalize JSON schema across runtime data:
  - `python tools/normalize_json_schema.py`
- Regenerate training interaction copy:
  - `python tools/apply_crude_training_copy.py`

### Run editor and asset tools
- Launch editor directly:
  - `python devkit/fantasy_manager_editor_v6.py`
- Launch editor via batch helper:
  - `devkit/ejecutar_editor.bat`
- Build Windows editor executable:
  - `devkit/build_editor_exe.bat`
- Harmonize worker images (JPG conversion/compression):
  - `python devkit/image_harmonizer.py`
  - `python devkit/image_harmonizer.py game/images/workers --include-jpg --jpg-max-kb=350`

### Ren'Py cache reset when script changes are not reflected
- PowerShell:
  - `Get-ChildItem -Path "game/scripts" -Filter "*.rpyc" -Recurse | Remove-Item -Force`
  - `Remove-Item -Path "game/cache/*.rpyb" -Force`

### Build/lint/test status
- There is **no single repository-wide lint/test command** checked in (no `pyproject.toml`, `package.json`, or dedicated test suite).
- Validation is primarily done through targeted Python validators and in-game verification.

## Architecture (big picture)

### 1) Data-driven runtime core
- `game/scripts/script.rpy` is the primary bootstrap layer:
  - Loads/merges buildings (`data/buildings/*.json`, excluding `daily_story_extensions`)
  - Loads items from `data/items/*.json`
  - Defines broad utility functions used by gameplay systems (conditions, inventory/item effects, image resolution, calendar/time helpers).
- Most balancing/content behavior is configured in JSON and interpreted at runtime rather than hardcoded per event/story.

### 2) Worker pipeline
- Worker content source is `game/data/workers/*.json` (legacy `data/workers.json` also supported).
- `game/scripts/workers/worker_loader.rpy`:
  - Aggregates worker files
  - Applies mode filters (NSFW/SFW, gender filters)
  - Applies default fields and trait normalization (including minimum trait population logic).
- Worker assignment and building sync logic is spread across:
  - `game/scripts/buildings/building_logic.rpy`
  - `game/scripts/core/screens.rpy` (`rebuild_assigned_servants`)
  - Save/load callbacks (see below).

### 3) Event pipeline
- Event files are loaded from `game/data/events/**` by `game/scripts/events/events_logic.rpy` (`load_events_from_folder`).
- Candidate filtering occurs in `select_possible_events` and includes:
  - Building type constraints
  - Cooldowns/occurrence limits
  - Required/excluded flags
  - Worker/building trait gates
  - Player gender gate.
- Runtime event execution is handled in `game/scripts/events/events.rpy` (`label handle_random_event`) and choice effects resolve through event effect logic (`event_resolution.rpy` + shared effect functions).

### 4) Daily simulation loop
- `game/scripts/events/event_daily_exec.rpy` (`process_daily_events`) drives next-day resolution:
  - Relinks assigned workers to canonical store objects
  - Processes workers by building/job
  - Applies difficulty multipliers, costs, outcome logic, and report generation inputs.
- Daily story `consequences` (per outcome) may include `trait_chance`: same list schema as training (`trait`, `chance_percent`, optional `duration`). Implemented via `store.apply_trait_chance_entries` (`worker_training.rpy`); granted traits are appended to the daily report description when successful.
- `trait_remove_chance`: same list shape without `duration`; uses `store.apply_trait_remove_chance_entries`. Successful removals are listed on the daily report. Interaction `effect` and training `training_results` blocks may use the same keys.
- This file is central when debugging “day advance” issues (economy, worker energy/health flow, daily reports).

### 5) Save/load model (critical)
- The project uses a custom JSON snapshot system in addition to Ren'Py saves:
  - `game/scripts/save_snapshot.rpy` manages snapshot slot GUIDs, validation, sanitization, and restore helpers.
  - Snapshot files live under `game/saves/` as `snapshot_*.json`.
- `game/scripts/save_state.rpy` registers `config.after_load_callbacks` to re-sync state after load (building assignments, worker defaults, trait cache preload).
- A large class of bugs in this codebase are sync bugs between:
  - `store.workers[*].assigned_building`
  - `available_buildings[*].assigned_servants`
  - `available_buildings[*].servant_jobs`

## Content and schema conventions to preserve

### Ren'Py pitfalls (“La Biblia”)
- **Read first** when touching save/load, workers, buildings, inventory, or any `store.*` gameplay state: [`docs/LA_BIBLIA_DE_LO_QUE_NUNCA_SE_DEBE_HACER.md`](docs/LA_BIBLIA_DE_LO_QUE_NUNCA_SE_DEBE_HACER.md). It documents recurring Ren'Py bugs in this project.
- **Do not** use `isinstance(x, dict)` or `isinstance(x, list)` to filter or iterate gameplay data from the store; workers, buildings, `worker["inventory"]`, nested rows, etc. are often `RevertableDict` / `RevertableList` and will fail those checks.
- **Do** use dict-like checks (`hasattr(x, "get")` and meaningful keys) and list-like iteration (`list(container)` or `hasattr(x, "__iter__")` / `__getitem__` as appropriate), and prefer `.get("key", default)` over bare `["key"]` when the key may be absent.
- **Building names**: accept both `"Building 1"` and `"Building_1"` (or use `_norm_building_key()` if the codebase already exposes it).
- **Screens**: avoid relying on variable scope/timing quirks; compute in the same `python:` block that consumes the data or write via actions into `store` (see the Biblia §4).

### Ren'Py object semantics
- Same rules as above: prefer duck-typing over strict `isinstance(..., dict/list)` wherever runtime objects may be Ren'Py revertable types. For detail and examples, use the Biblia link in the previous subsection.

### JSON authoring workflow
- Canonical references:
  - `docs/json_schema_canonical.md`
  - `game/data/json_schema_standard.md`
  - templates in `docs/templates/**`
- Keep content schema-complete (neutral defaults allowed) and validate modified event files with `devkit/validate_event_mechanics.py`.

### Worker data placement conventions
- Worker categories are split across:
  - `workers_sfw_unique.json`
  - `workers_sfw_other.json`
  - `workers_nsfw_unique.json`
  - `workers_nsfw_other.json`
- Worker `folder` must match `game/images/workers/<folder>/` exactly.
