# Fantasy Manager — Revamp: Audit Summary

This is a **side-by-side revamp** of the original `fantasy-manager` project (the original was never modified). It keeps full compatibility with the existing JSON data and image assets. Fresh git repo; the baseline commit `9a01798` is a verbatim copy of the original working tree, so **every change is `git diff 9a01798 HEAD`**.

- Engine: Ren'Py 8.3 (SDK used: `D:\renpy-8.3.4-sdk`).
- Lint: `renpy.exe <projectdir> lint` — **clean** at every commit.
- Net diff vs baseline: ~3.4k insertions / ~3.4k deletions across 50 source files (the rest is dead code removed).
- Two more docs in the repo root: `REVAMP_NOTES.md` (detailed), `RELEASE_NOTES.md` (player-facing).

Audit tips:
- Review by commit — each commit is single-purpose with a descriptive body. `git log --reverse --stat`.
- The biggest single file is `game/scripts/core/screens.rpy` (UI); most engine logic is in `script.rpy`, `event_daily_exec.rpy`, `events.rpy`.
- Project coding rules live in `docs/LA_BIBLIA_DE_LO_QUE_NUNCA_SE_DEBE_HACER.md` (§1–§10). §10 was added this session.
- **The baseline `9a01798` already contains the full Yvara and Lanista arcs (`yvara_complete.rpy`, `lanista_complete.rpy`, ~3k lines each) — that content is INHERITED, not new.** The only arc changes in this revamp are the ones listed under §A "Story arcs" (a call-stack fix, wager money-gating/EV, day-gating, grind rebalance, intro popup, mojibake) and the data adds (Marigold rename, 4 dominion post-arc events). Do not spend time auditing the arcs' prose or overall design — focus on the ~50 files in `git diff 9a01798 HEAD`.

---

## A. Engine / logic changes

### Crash & correctness fixes (`script.rpy`, `events.rpy`, `event_daily_exec.rpy`, `events_logic.rpy`)
- **`after_date:` condition** — referenced an undefined `required_month_0based` (real var was `required_month_1based`); silently false for the whole target year. Fixed the 0-based conversion.
- **`building_skill` choices** — indexed `choice["option"/"message_success"/"message_failure"]` directly → KeyError on modded/hand-edited events. Now `.get()` with safe defaults; also removed a one-event "Unknown → badly burnt" message-hijack hack and made the debug logging use `.get()`.
- **`process_choice` return type** — returned a bare string on the unknown-`worker_selection` error path while the caller does `.get()` → AttributeError. Now returns a dict like every other path.
- **Null/empty `condition` in a `random` event** — fell into the skill-check path with skill 0 → guaranteed failure. Now routes to the no-check branch.
- **`consume_item` / `grant_loot`+consume** — unpacked 3-tuple inventory entries into 2 names (ValueError, silently swallowed for `consume_item`; hard crash for `grant_loot`). Both now delegate to `remove_item_from_inventory`.
- **NameError on zero-weight event pools** — `chosen_event_tuple` referenced before assignment when every candidate had `weight 0`. Guarded.
- **`basestring`** (Py2 relic) → `str`.

### Event selection / pool rework (`event_daily_exec.rpy`, `events_logic.rpy`)
- **Guaranteed-pool starvation** — a guaranteed event with no eligible worker used to shadow the priority/normal pools, blocking *all* events. Removed the re-lock.
- **Priority events double-gated** — story/quest/`priority:true` events without an explicit probability were rolled twice AND manager-reduced (against design). Now each event rolls its own probability once (default 50%), not manager-reduced.
- **Manager reduction unified** to 10%/manager (was 15% at pool level, 10% at event level).
- **`exact_date` fallback** scanned `all_events` (bypassing occurrence caps/flags) → consumed one-shots re-fired every anniversary. Now scans the filtered list.
- **Decline-to-reappear** — the `{id}_passed` cooldown reader in `select_possible_events` was dead (nothing set the flags). Cancel/decline paths now set `{id}_passed` + timestamp.
- **`limited` inference** — the loader now treats an authored `max_occurrences` as implying `limited: true`; unknown `worker_selection` values (e.g. the shipped `"player"`) are normalized to `"choose"`.
- **`"the worker"` replacement** is now word-bounded (a blanket `.replace` mangled "the workers" → e.g. "Aeliss").
- **Difficulty-scaled minimum floor** for worker/building skill checks (nightmare 10% … story 50%), for parity with probability events.
- **`failed_rolls`** dead mechanic removed.

### Governor tension (`tutorial_system.rpy`, `event_daily_exec.rpy`)
- **Sabotage** reduced a building's `skill_bonus` "for 3 days" but never restored it. Now records the actual reduction and restores it in the daily loop.

### Recruitment engine (`recruitment_functions.rpy`, `recruitment_flow.rpy`)
- Min-chance floor + reuse of the main engine's central skill-check; trait-adjusted eligibility; `player_gender_requirement` and `worker_filter` (previously dead data) now honored; occurrence caps respected; `joy` effect applied; "examine" no longer consumes the day's attempt; `[player_title]/[player_name]` substitution added; 5 dead functions removed.

### Workers / traits / buildings (`worker_*.rpy`, `building_logic.rpy`, `script.rpy`)
- **Unique-worker trait skip** was promised in comments but not implemented — the Lanista got 2–4 random traits. `ensure_minimum_traits` now early-returns for `unique` workers.
- **Empty trait-pool guard** in `ensure_minimum_traits` (IndexError on exhausted pools).
- **Interaction flag gating** — `required_flags/excluded_flags` compared dict-shaped flags raw (never matched). Now unwraps `{"value":…}`; two self-gating "Special" interactions now gate correctly.
- **Worker-flag duration expiry** implemented (51 `duration` keys in JSON were never processed) — `expire_worker_flags()` runs daily.
- **Health/energy caps** vs calculated max in `apply_interaction_effects` and `training_apply_effect_dict` (were clamped to a hard 100).
- **`daily_cost`** used `comfort * 20` (wrong on non-normal difficulty) → `int(comfort * get_difficulty_comfort_mult())`.
- **Building-key normalization** routed through `_resolve_building_by_name` in `building_logic.rpy` (accepts "Building 1" / "Building_1").
- **Per-worker level-ups**: extracted `update_skill_levels_for_worker`; training no longer runs a full-roster pass per single use.
- Trait-cache invalidation now also clears `_training_meta_flow_entry`; NSFW options toggle refreshes trait+interaction caches.

### Save system (`save_snapshot.rpy`)
- Lanista list fields restored via the deepcopy list loop (parity with Yvara); `after_load` re-read uses the `_for_reading` path (legacy save location); dead stubs (`snapshot_pre_save*`, `PageAwareFileAction`) removed.

### Story arcs (`yvara_complete.rpy`, `lanista_complete.rpy`, `academy_library_quest.rpy`)
- **Call-stack leak**: Yvara S4 gate did `jump` inside a `call`-ed label (abandoning the frame) — fixed to match the S5/S6 flavor-only pattern. Two finished-but-unreachable Yvara mechanics wired into the visit menu.
- **Lanista**: wagers money-gated + EV rebalanced (no positive-EV pump); post-arc Talk day-gated; early-stage grind roughly halved; dominion card choices grant affection; intro popup registered; comment mojibake normalized; two lint `%` warnings fixed.
- Academy "six-letters" note reworded to be true; an unreachable statement and a global bold-style override removed.

### Dead code removal (`main_flow.rpy`, `script.rpy`, `config.rpy`, `worker_management.rpy`, `tutorial_*`)
- Deleted files: `game/scripts/core/daily_report.rpy` (all fns zero-callers), `game/scripts/file_save_system.rpy` (disabled stubs; live `interaction_*` styles rescued into `screens.rpy` first).
- Deleted: dead BGM machinery, `Player` class shadowing `Character`, `combat_check`/`get_best_worker_with_skill`/`reset_calendar_to_start`/`format_money`, dup `check_trait_durations`, `navigate_worker`/`get_sell_info`, dead tutorial labels.
- **Deduplicated**: start-of-day automation (5 copies → `run_start_of_day_automation`), Governor Castle unlock (3 divergent copies → `unlock_governor_castle`, idempotent, preserves upgrades), message chunking.

### Call-stack hygiene (`screens.rpy`, `main_flow.rpy`)
- Hub `Call(...)` actions → `Jump(...)` (they never returned); objective dialogues `return` instead of `jump`; `tavern_screen` clears leaked return frames on entry and never returns past the hub. This addresses the historical "mixed dialogue / stacked frames in traceback" class.
- `Ctrl+M` (was plain `M`) for the emergency music stop.

### Data fixes (`game/data/**`)
- 10 `worker_selection:"player"` events (invalid mode) fixed to `choose` + `threshold`; 20 one-shots marked `limited`; `Wounded` trait defined (3 events granted a nonexistent trait); phantom arena `relevant_traits` mapped to real traits; unreachable duplicate worker "Daisy" (unique, folder `lily`) renamed **Marigold** + its recruit/lore events retargeted; `Accommodations` typo; `arcane_breach` nsfw-flagged; ~15 find-and-replace-damaged prose strings rewritten; quotes normalized; orphan Lanista trait removed; **4 new dominion post-arc ambient events** (2 per arc); shop-event outcomes differentiated per choice; recruitment stock phrases rotate variants.

### Audio (new subsystem)
- BGM now loops with a 90s breathing gap and auto-recovers after load (was: played once per session then silence forever; a phantom `main_theme.ogg` fallback removed).
- New `game/scripts/core/audio.rpy`: global button click via style + `play_ui_sound()` helper. 6 procedurally-generated WAV cues in `game/audio/sfx/` (click, coin, notify, day-chime, success, failure). Day-transition chime + success/failure stingers on event outcomes.

---

## B. UI changes (`screens.rpy`, `gui.rpy`)

### Design system (new, in `gui.rpy`)
- **Design tokens**: `gui.ink_color`, `gui.parchment_muted_color`, `gui.success_color`, `gui.danger_color`, `gui.warning_color`, `gui.gold_color`, `gui.success_bright`, `gui.danger_bright`, `gui.surface_dark`, `gui.health_bar_color`, `gui.energy_bar_color`, `gui.bar_track_color`, `gui.row_alt_color`, `gui.divider_color`, plus the pre-existing `gui.journal_text/hover/dark_color`. (Note: `gui.muted_color` is a **different** pre-existing engine var for bar regeneration — not reused.)
- **Shared components** (screens):
  - `screen table_rule(rule_width, rule_xalign, rule_xoffset)` — the single header/divider hairline used across all tables. Soft 1px shoulders around a 2px core so window downscaling can't rasterize it thinner/paler on one screen than another (a real bug we hit — see §10 in LA BIBLIA).
  - `screen worker_portrait_thumb(portrait_path, initial)` — 52px framed portrait miniature (clipping viewport crops wide art to a square biased upper-center; letter placeholder without art). Uses `get_worker_portrait_cached(worker)` (one folder scan per worker per session).

### Unified table look (workers roster, daily report, buy servants)
All three tables now share: plain-label headers over one `table_rule` (removed per-column `tablebutton` underline art), framed portrait thumbnails, zebra striping, one divider token, and semantic colors. Group headers in daily report use a **hanging indent** (a little left of the Building column, clear of the margin).

### Workers screen (`screen workers`)
- Rows redesigned: portrait, name, building, job(skill), **E/H as thin token-colored bars** with the number turning `danger_color` below 30%, and Type/Action.
- Fixed several composition bugs found via screenshot verification: viewport height budget (rows overflowed the parchment border), removal of negative draw offsets that desynced layout vs draw, the table centered in the frame, and the **scrollbar placed at the right edge under the close X** (measured to ~3px). Building-column value alignment reverted (see daily-report note). A pre-existing bug where the list opened scrolled ~1.5 rows was fixed (a redundant `restart_interaction` in on-show).

### Daily report (`screen daily_report`)
- Summary band (income green / costs red / net by sign / active count); rows grouped by building with muted hanging-indent group headers; per-entry earnings colored by sign; **per-worker delta badges** next to the name (+Lv gold, +N skills green, −N HP red) fed by a new session-only `daily_worker_deltas` tracker in `process_daily_events`. Type scale raised (data 21, badges 17, headers 22). Filters nudged up 5px with +5px air before headers.

### Theme harmonization
- 17 cold-dark modal backdrops unified to `gui.surface_dark`; 18px text raised to 20 where cell budgets allow; the 4 filter dropdown menus share one hover/selected treatment; tavern/map hub buttons had a hover wash added then **removed** (user preference) — kept only on small controls.
- Map: locked/in-development destinations rendered desaturated (`SaturationMatrix(0.35)`), actions/tooltips/focus-masks untouched.
- Side info panel (date/money/worker+building counts) made consistent across the 4 screens that show it.

### QoL / interaction
- **Backspace closes any screen** (45 screens, each mirroring its own close/X/Cancel action); **Ctrl+Left/Right** = Previous/Next in worker/report details (guarded like the buttons). Skipped: screens with text inputs, event-decision screens (destructive), the gender-filter warning.
- **Job-selection tooltip** — hover a profession to preview relevant skill values, building bonus, and estimated daily success %. Rendered as a fixed panel (mirrors the generic tooltip styling) whose Y follows the mouse.
- **Mass-sell** in shop mode: Sell stack / Sell shown / Sell dupes, with a confirm dialog; the executor is store-level (a screen-local fn inside a `Confirm` would be pickled — BIBLIA §8), re-verifies at execution, never sells equipped/quest/test items.
- **Repeat last interaction** button in worker details (session-recorded, shown only when the interaction is currently available for that worker, relaunched through the exact menu action — no gating bypassed; training interactions excluded).
- **"Don't ask again"** on the potion-buy confirm + a toggle in options.
- **E/H color coherence** applied to worker details and the inventory quick panel (token bar colors + danger-color numbers).
- **Buy Servants** rows got framed portraits + control fonts scaled into family (20 → 24).
- **adjust_comfort** spacing tightened so the Adjust row fits within the frame.

### Verification method (for the auditor)
Geometry/visual changes were checked with a throwaway `game/zz_ui_probe.rpy` splashscreen that fabricates fake data, shows a target screen, and parks; a PowerShell `PrintWindow` capture of the real game window was then reviewed as an image and **pixel-sampled** (System.Drawing GetPixel) to compare colors, thicknesses, and element positions. Two lessons were folded into the process: verify the *rendered pixels* not the declared code (identical `Solid`s can rasterize differently after downscaling), and verify the change *on the specific screen requested*. The probe file and its screenshots are gitignored and not part of the source.

---

## Responses to external audit (7 verification points)

An external reviewer confirmed the work and raised 7 edge-case checks (none were bugs). Resolution:

1. **BGM resume on load** — `after_load` ends in `jump tavern_screen`, which calls `ensure_bgm_playing()`, so it already resumed on every load (this JSON-snapshot save system always lands in the tavern hub — there are no mid-scene saves). Hardened anyway: `ensure_bgm_playing()` is now called explicitly in `after_load` before the jump, so resumption no longer depends on hub routing.
2. **Health/energy caps** — reviewed `calculate_max_health`/`calculate_max_energy` (`worker_stats.rpy:175/221`): both recalculate from scratch (base-from-level + trait + equipped-item + management-skill bonuses), apply an optional trait cap (ignoring ≤0 schema-default caps), and floor with `max(1,…)`/`max(0,…)`. Clamping interaction/training gains to these instead of a hard 100 is correct; the "gives more on blessed workers" behaviour is the intended fix (a worker with max>100 was previously healed only to 100). No change.
3. **`import re as _re` inline** in `events.rpy` — correct as-is (label python block). Noted: if that block is ever hoisted to `init python`, move the import too. No change.
4. **Alpha-hex Solids (`#RRGGBBAA`)** — the packaged runtime is Ren'Py 8.3.7 (lint banner `8.3.7.25031702`), which supports 8-digit hex. Confirmed. Only a concern if a pre-8.2 runtime is bundled, which it isn't.
5. **`table_rule` 3-Solid feathered line at fractional scale** — the soft 1px half-alpha shoulders around the 2px core are *specifically* the mitigation for downscale-phase banding. Verified by pixel-sampling: the workers and daily-report rules render byte-identical profiles (shoulder 194,164,126 / 2px core 177,150,112 / shoulder) at the captured window scale. A final visual spot-check at 1280×720 is still a reasonable QA step and is recommended before release.
6. **`daily_worker_deltas` reset** — documented in code (`event_daily_exec.rpy` ~478): session-only, reset at the single once-per-day entry (`process_daily_events`, called once from `label next_day`); if ever chained twice per day only the last pass's badges would show. Display-only, not saved.
7. **Baseline includes the arcs** — clarified at the top of this doc: the Yvara/Lanista arcs are inherited from `9a01798`, not new; audit only `git diff 9a01798 HEAD`.

## Intended behaviour changes (confirmed by differential analysis, not bugs)

A second reviewer diffed the revamp against the original function-by-function and found **no crash regressions**. Four player-visible behaviour changes, all intended:

1. **BGM now loops** (was: only the first/last Monday of each month, then permanent silence via a fallback to a non-existent `main_theme.ogg`). The old behaviour was a bug. If a player wants silence, lower the music volume.
2. **Priority events no longer double-gated** — a priority event with no explicit `event_probability` used to roll twice (a shared pool roll + an individual manager-reduced roll). Now one roll per event, no manager reduction → priority events fire at their authored frequency.
3. **Manager reduction unified to 10%/manager** (was 15% pool + 10% individual). The 1% floor is unchanged; with 1–2 managers there are slightly more events. A mild buff, not a nerf.
4. **`daily_cost` scales with difficulty** (Nightmare ×30 … Story ×15; Normal ×20 = unchanged). The original hardcoded `comfort*20` only in `adjust_comfort`; every other site already used `get_difficulty_comfort_mult()`. This is a consistency fix — Nightmare players will see newly-hired/adjusted workers cost more.

## Smoke-test dispositions (differential-audit recommendations)

| # | Test | Disposition |
|---|------|-------------|
| 1 | Load an original save; no traceback in `after_load` (esp. new `ensure_bgm_playing`) | **Covered by design.** `ensure_bgm_playing` is fully guarded (try/except + `is_playing` check + `start_bgm_simple`'s own guards) and the `after_load` call wraps it in another try/except. Boot smoke test passes with no traceback. Live cross-save load still worth a human click-through. |
| 2 | Nightmare + 3 managers, 5–7 days, events still appear | **Needs live play** (multi-day). Logic confirmed statically by both audits; the 1% floor is preserved. |
| 3 | Decline an event, advance 3–5 days, verify it reappears | **Needs live play.** Logic path: cancel sets `{id}_passed` + timestamp; `select_possible_events` reads them with a per-tier cooldown. |
| 4 | Governor sabotage, verify skill_bonus restores after 3 days (notify visible) | **Needs live play.** Writer records the real reduction; the daily loop restores it and `renpy.notify`s. Confirmed static by the auditor. |
| 5 | Button click doesn't saturate/glitch on rapid clicks | **Verified.** All 6 WAVs are 16-bit/44.1kHz; `ui_click` is 60ms, peak 0.15, edge amplitude <0.01 (fade-in + near-zero tail → no pop; overlapping clicks sum well under clipping). Channel routing documented: UI cues play on `"audio"`, event music on `"sound"` — no collision for the stingers/chime; the click's brief overlap with the 1s non-looped event clip is negligible. |

## Known non-blocking items
- Buy Servants uses a larger type scale (28/26) than the other tables (22/21) — deliberate (5-row table with lots of air); flagged in case the auditor prefers uniformity.
- The Assign-Role tooltip is only shown on hover, so it wasn't captured by the offline probe (structure is identical to the verified generic tooltip).
- Old saves from the original load (same JSON-snapshot save system); a save that had recruited the unique "Daisy" (was unreachable) won't find her renamed template.
