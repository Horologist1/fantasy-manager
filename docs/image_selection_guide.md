# Image Selection Guide

This guide explains how the game resolves event/report images, including worker folders, trait prefixes, skill aliases, and fallback behavior.

## 1) Where resolution logic lives

- `game/scripts/events/event_visuals.rpy`
  - `get_event_image(worker, event, outcome, skill_name)`
  - `get_event_background(event, outcome, worker)`
  - `get_trait_prefixes(worker)`
  - `get_image_matches_flexible(...)`
  - `get_pattern_matches_flexible(...)`
- `game/scripts/script.rpy`
  - `get_fallback_folder(worker)` (`male -> guy`, otherwise `blossom`)
- `game/scripts/events/events_logic.rpy`
  - Event availability filters (including worker/building trait gating)

## 2) Main folder strategy

Primary worker path:
- `images/workers/<worker_folder>/`

Fallback folder:
- `images/workers/guy/` for male workers
- `images/workers/blossom/` for female/unknown workers

Event/root fallback paths:
- `images/events/<name>.<ext>`
- `images/<name>.<ext>`

Supported media extensions:
- `.png`, `.jpg`, `.jpeg`, `.webp`, `.webm`, `.mp4`

## 3) Priority order

## Daily/worker image resolution (`get_event_image`)

1. Worker folder + trait-prefixed event image candidates
2. Worker folder + non-trait event image candidates
3. Worker folder + trait-prefixed skill image candidates
4. Worker folder + non-trait skill image candidates
5. Default fallback folder + trait-prefixed event candidates
6. Default fallback folder + non-trait event candidates
7. Default fallback folder + trait-prefixed skill candidates
8. Default fallback folder + non-trait skill candidates
9. Rest-specific image handling (`rest_*`, then generic `rest`)
10. Worker/default `profile` fallback

## Event scene background resolution (`get_event_background`)

1. If event has worker context: try worker-specific media first (`get_event_image`)
2. Resolve event keys by outcome:
   - success: `success_image` / `success_background`
   - failure/mediocre: `failure_image` / `failure_background`
   - default: `background_image`
3. Generic media fallback:
   - `generic_success` or `generic_failure`
4. Final fallback:
   - `event_bg`

## 4) Outcome mapping details

- Success branch uses outcomes: `success`, `critical_success`
- Failure branch includes: `failure`, `mediocre`
- For some searches, filenames containing `failure` are excluded from success candidates.

## 5) Trait prefixes used for image selection

Trait detection priority:
1. `Transformed`
2. `Magical`
3. `Futa`
4. `Pregnant`

Generated prefixes include:
- Singles: `transformed_`, `magical_`, `futa_`, `pregnant_`
- Combinations (examples):
  - `transformed_magical_`
  - `transformed_futa_`
  - `magical_pregnant_`
  - `transformed_magical_futa_pregnant_`

Important:
- Pregnant images should use `pregnant_` prefix.

## 6) Skill name normalization and aliases

Skill normalization examples:
- `Service` -> search patterns include `wait`, `service`, `maid`
- `Homo` -> `les`, `gay`
- `Special` -> `special`, `titty`
- `Striptease` -> `strip`, `striptease`
- `Extreme` -> `extreme`, `beast`

## 7) Recommended naming conventions

Use lowercase and consistent separators:
- Event success example: `brothel_caution.png`
- Event failure example: `brothel_caution_failure.png`
- Trait + event success: `pregnant_brothel_caution.png`
- Trait + event failure: `pregnant_brothel_caution_failure.png`
- Skill success example: `service.png`
- Skill failure example: `service_failure.png`
- Trait + skill success: `magical_service.png`
- Trait + skill failure: `magical_service_failure.png`

## 8) Debug checklist when an image does not appear

1. Confirm file is in worker folder or fallback folder.
2. Confirm extension is one of the supported media extensions.
3. Confirm outcome suffix (`_failure`) matches expected branch.
4. Confirm trait prefix order/name is valid.
5. Confirm `story_image`, `success_image`, `failure_image` values match filenames.
6. If event scene media fails, verify `images/events` and `images` candidates.
7. If still unresolved, test with plain `profile` image as baseline.
