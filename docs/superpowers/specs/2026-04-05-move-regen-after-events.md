# Move Daily Energy/Health Regeneration to After Events

**Date:** 2026-04-05
**Status:** Approved

## Problem

Workers regenerate health/energy/libido BEFORE daily events run. This means:

1. Player sees workers with low energy, gives them potions
2. `process_next_day` regenerates energy (partially wasting the potions)
3. Events consume energy
4. Next day workers are low again

The energy values shown on the worker screen do not reflect what workers will actually have when events run.

## Solution

Move the health/energy/libido regeneration block from BEFORE `process_daily_events()` to AFTER `check_worker_health()` (dead check) within `process_next_day` in `event_daily_exec.rpy`.

## File Changed

`game/scripts/events/event_daily_exec.rpy` — function `process_next_day` only.

## New Execution Order in `process_next_day`

1. Reset building costs
2. Auto-rest manager
3. Auto-equip
4. **Recalc `max_health`/`max_energy`** (new mini-block, needed for display and event clamping)
5. Reset `failed_rolls`, relationship fixes, comfort bonuses, `apply_worker_daily_effects`
6. Relink workers to buildings
7. **`process_daily_events()`** — events consume energy/health
8. Calculate income/costs
9. **`check_worker_health()`** — workers at 0 health die
10. **Regenerate health/energy/libido** — moved here ("nightly rest")
11. Level ups, finances, governor tension, random events

Auto-consume of potions (in `main_flow.rpy`, after daily report) remains unchanged and naturally runs after regeneration.

## Detailed Changes

### 1. Remove regen from pre-events block (lines ~1512-1550)

Cut the entire regeneration block:
- Health regen (lines 1513-1526)
- Energy regen (lines 1528-1547)
- Libido regen (lines 1549-1550)

### 2. Add max_health/max_energy recalc in pre-events block

Replace the removed regen block with a lightweight recalc:

```python
# Recalculate max health/energy for display and event clamping
for worker in store.workers:
    worker["max_health"] = calculate_max_health(worker)
    worker["max_energy"] = calculate_max_energy(worker)
```

### 3. Insert regen block after dead check (after line ~1621)

Paste the regeneration block after `check_worker_health()` and its messages, before `update_skill_levels()`. Update the comment from "BEFORE events" to "AFTER events and dead check (nightly rest)".

The regen block also recalculates `max_health`/`max_energy` (in case temporary traits changed during events).

## Behavioral Changes

- **Workers may start the day with 0 energy:** Intended. Player sees real energy and decides whether to use potions. Workers at 0 energy skip events (existing mechanic at line 627).
- **More deaths possible:** Workers that previously survived because regen ran before events may now die if events drain health to 0. Chosen deliberately (Approach 2).
- **Libido regen more coherent:** Now uses same-day `daily_sexual_work` instead of previous day's count.
- **Potion efficiency improved:** Potions given by the player are no longer partially wasted by pre-event regen.

## Save Compatibility

No data structure changes. Only execution order changes within `process_next_day`. Existing saves are fully compatible.

## Documentation Updates

Update `docs/FANTASY_MANAGER_GAME_REFERENCE.md` section 18 "Game Flow" to reflect that regeneration now happens after events, not before.
