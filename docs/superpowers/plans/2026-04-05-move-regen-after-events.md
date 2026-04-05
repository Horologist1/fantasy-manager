# Move Daily Regen After Events — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move health/energy/libido regeneration from before daily events to after events and the dead check, so the worker screen shows energy workers will actually have for daily stories.

**Architecture:** Single function reorder in `process_next_day` (`event_daily_exec.rpy`). The regen block (lines 1512-1550) is cut from its current position and inserted after `check_worker_health()` (after line 1621). A lightweight `max_health`/`max_energy` recalc replaces it in the pre-events position.

**Tech Stack:** Ren'Py (Python 2/3 hybrid), no test framework available — verification via in-game log inspection.

**Spec:** `docs/superpowers/specs/2026-04-05-move-regen-after-events.md`

---

### Task 1: Replace regen block with max recalc in pre-events section

**Files:**
- Modify: `game/scripts/events/event_daily_exec.rpy:1512-1550`

- [ ] **Step 1: Replace the regen block (lines 1512-1550) with a max_health/max_energy recalc**

Replace this entire block:

```python
        # Regenerate energy/health and update stats BEFORE events
        for worker in store.workers:
            old_health = worker["health"]
            base_regen = worker.get("level", 1)
            trait_regen = calculate_health_regeneration(worker)
            health_regen = base_regen + trait_regen
            max_health = calculate_max_health(worker)
            worker["max_health"] = max_health
            new_health = min(worker["health"] + health_regen, max_health)
            worker["health"] = new_health
            # Always log health regeneration to verify it's working
            if old_health != new_health:
                renpy.log(f"HEALTH REGEN: {worker.get('name', 'Unknown')} health {old_health} -> {new_health} (regen: +{health_regen} = level {base_regen} + trait {trait_regen}, max: {max_health})")
            else:
                renpy.log(f"HEALTH REGEN: {worker.get('name', 'Unknown')} health {old_health} (already at max {max_health}, regen would be +{health_regen} = level {base_regen} + trait {trait_regen})")

            old_energy = worker["energy"]
            base_energy_regen = worker.get("level", 1)
            try:
                _comfort_lv = int(worker.get("comfort_level", 1))
            except Exception:
                _comfort_lv = 1
            # Comfort 1 is minimum/baseline; only levels above 1 add to daily energy regen
            comfort_energy_regen = max(0, _comfort_lv - 1)
            trait_energy_regen = 0
            try:
                trait_energy_regen = calculate_energy_regeneration(worker)
            except Exception:
                trait_energy_regen = 0
            energy_regen = base_energy_regen + comfort_energy_regen + trait_energy_regen
            max_energy = calculate_max_energy(worker)
            worker["max_energy"] = max_energy
            new_energy = min(worker["energy"] + energy_regen, max_energy)
            worker["energy"] = new_energy
            if old_energy != new_energy:
                renpy.log(f"ENERGY REGEN: {worker.get('name', 'Unknown')} energy {old_energy} -> {new_energy} (regen: +{energy_regen} = level {base_energy_regen} + comfort {comfort_energy_regen} + trait {trait_energy_regen}, max: {max_energy})")

            if persistent.nsfw_enabled:
                regenerate_libido(worker)
```

With this lightweight recalc:

```python
        # Recalculate max health/energy for display and event clamping (regen moved to after events)
        for worker in store.workers:
            worker["max_health"] = calculate_max_health(worker)
            worker["max_energy"] = calculate_max_energy(worker)
```

**Important:** The lines that follow the removed block (`worker["failed_rolls"] = 0` at line 1552 onward through line 1583) stay exactly where they are. They just need to be inside a `for worker in store.workers:` loop. Currently they share the loop with the regen block. After removing regen, they need their own loop OR the max recalc loop above must be merged with them into one loop.

The cleanest approach: keep one `for worker in store.workers:` loop that does max recalc + the existing attribute resets. The replacement becomes:

```python
        # Recalculate max health/energy and reset daily counters (regen moved to after events and dead check)
        for worker in store.workers:
            worker["max_health"] = calculate_max_health(worker)
            worker["max_energy"] = calculate_max_energy(worker)

            worker["failed_rolls"] = 0
```

And the rest of the loop body (lines 1554-1583: comfort, romance, relationship, joy fixes, `apply_worker_daily_effects`, comfort bonus) continues unchanged inside the same loop.

- [ ] **Step 2: Verify indentation and loop structure**

Confirm the `for worker in store.workers:` loop now contains:
1. `max_health`/`max_energy` recalc (new)
2. `failed_rolls = 0` (existing, unchanged)
3. Romance/rebelliousness/joy fixes (existing, unchanged)
4. Minimum relationship enforcement (existing, unchanged)
5. `apply_worker_daily_effects` (existing, unchanged)
6. Comfort bonus to joy (existing, unchanged)

No regen code remains in this loop.

---

### Task 2: Insert regen block after dead check

**Files:**
- Modify: `game/scripts/events/event_daily_exec.rpy:1621` (after dead worker messages, before `update_skill_levels()`)

- [ ] **Step 1: Insert the regen block after the dead workers section**

After this existing code:

```python
        # Check for dead workers
        dead_workers = check_worker_health()
        if dead_workers:
            if len(dead_workers) == 1:
                renpy.say(None, f"{dead_workers[0]} has died and had to be let go.")
            else:
                names_text = ", ".join(dead_workers[:-1]) + f" and {dead_workers[-1]}"
                renpy.say(None, f"{names_text} have died and had to be let go.")
```

And before this existing code:

```python
        # Update skill levels and worker levels
        update_skill_levels()
```

Insert the full regen block:

```python
        # --- NIGHTLY REST: Regenerate health/energy/libido AFTER events and dead check ---
        for worker in store.workers:
            old_health = worker["health"]
            base_regen = worker.get("level", 1)
            trait_regen = calculate_health_regeneration(worker)
            health_regen = base_regen + trait_regen
            max_health = calculate_max_health(worker)
            worker["max_health"] = max_health
            new_health = min(worker["health"] + health_regen, max_health)
            worker["health"] = new_health
            if old_health != new_health:
                renpy.log(f"HEALTH REGEN: {worker.get('name', 'Unknown')} health {old_health} -> {new_health} (regen: +{health_regen} = level {base_regen} + trait {trait_regen}, max: {max_health})")
            else:
                renpy.log(f"HEALTH REGEN: {worker.get('name', 'Unknown')} health {old_health} (already at max {max_health}, regen would be +{health_regen} = level {base_regen} + trait {trait_regen})")

            old_energy = worker["energy"]
            base_energy_regen = worker.get("level", 1)
            try:
                _comfort_lv = int(worker.get("comfort_level", 1))
            except Exception:
                _comfort_lv = 1
            comfort_energy_regen = max(0, _comfort_lv - 1)
            trait_energy_regen = 0
            try:
                trait_energy_regen = calculate_energy_regeneration(worker)
            except Exception:
                trait_energy_regen = 0
            energy_regen = base_energy_regen + comfort_energy_regen + trait_energy_regen
            max_energy = calculate_max_energy(worker)
            worker["max_energy"] = max_energy
            new_energy = min(worker["energy"] + energy_regen, max_energy)
            worker["energy"] = new_energy
            if old_energy != new_energy:
                renpy.log(f"ENERGY REGEN: {worker.get('name', 'Unknown')} energy {old_energy} -> {new_energy} (regen: +{energy_regen} = level {base_energy_regen} + comfort {comfort_energy_regen} + trait {trait_energy_regen}, max: {max_energy})")

            if persistent.nsfw_enabled:
                regenerate_libido(worker)
        # --- END NIGHTLY REST ---
```

This is the exact same code that was removed in Task 1, with only the comment changed.

- [ ] **Step 2: Verify surrounding code**

Confirm the full sequence after events is now:
1. Income/cost calculation
2. `check_worker_health()` + dead worker messages
3. **Nightly rest regen block** (new position)
4. `update_skill_levels()` (unchanged)
5. `update_worker_levels()` (unchanged)

---

### Task 3: Update game reference documentation

**Files:**
- Modify: `docs/FANTASY_MANAGER_GAME_REFERENCE.md:754-760`

- [ ] **Step 1: Update section 18 "Game Flow"**

Replace the current Day Start section:

```markdown
1. **Day Start:**
   - Advance calendar (`advance_date()`)
   - Reset building costs to 0
   - Regenerate health/energy/libido for workers (BEFORE events)
   - Reset daily counters (failed_rolls, skill_uses)
   - Apply comfort bonuses to joy
   - Enforce minimum relationship (10 + comfort_level)
```

With:

```markdown
1. **Day Start:**
   - Advance calendar (`advance_date()`)
   - Reset building costs to 0
   - Recalculate max health/energy
   - Reset daily counters (failed_rolls, skill_uses)
   - Apply comfort bonuses to joy
   - Enforce minimum relationship (10 + comfort_level)
```

And update the existing sections to add a new step between "Calculate Finances" and "Update Workers":

Replace:

```markdown
3. **Calculate Finances:**
   - Sum all earnings from daily_report
   - Calculate total costs (base_cost + skill_bonus_cost + worker_costs)
   - Net = income - costs

4. **Update Workers:**
   - Check level ups (success_count >= 20 × level)
   - Check skill ups (success_count >= 10 × skill)
   - Apply secondary attribute changes
```

With:

```markdown
3. **Calculate Finances:**
   - Sum all earnings from daily_report
   - Calculate total costs (base_cost + skill_bonus_cost + worker_costs)
   - Net = income - costs

4. **Check Dead Workers:**
   - Workers with health <= 0 are removed

5. **Nightly Rest (Regeneration):**
   - Regenerate health: level + (1 + trait bonuses)
   - Regenerate energy: level + comfort bonus + trait bonuses
   - Regenerate libido (NSFW): considers same-day sexual work count

6. **Update Workers:**
   - Check level ups (success_count >= 20 × level)
   - Check skill ups (success_count >= 10 × skill)
   - Apply secondary attribute changes
```

Also renumber "Random Events" to 7 and "Show Daily Report" to 8.

---

### Task 4: Clear Ren'Py cache and commit

**Files:**
- Delete: `game/scripts/events/event_daily_exec.rpyc`
- Delete: `game/cache/*.rpyb`

- [ ] **Step 1: Clear compiled cache so Ren'Py picks up the changes**

```bash
rm -f game/scripts/events/event_daily_exec.rpyc
rm -f game/cache/*.rpyb
```

- [ ] **Step 2: Commit all changes**

```bash
git add game/scripts/events/event_daily_exec.rpy docs/FANTASY_MANAGER_GAME_REFERENCE.md
git commit -m "move daily health/energy/libido regen to after events and dead check

Regeneration now runs as 'nightly rest' after daily events process and
dead workers are removed, instead of before events. This means:
- Energy/health shown on worker screen reflects what workers have for work
- Potions given by the player are not wasted by pre-event regen
- Libido regen now uses same-day sexual work count (more coherent)
- Workers at 0 health after events die before regen can save them (stricter)"
```

---

### Task 5: In-game verification

No automated test suite exists. Verify manually by advancing one day in-game and checking `game/log.txt`.

- [ ] **Step 1: Launch the game and load a save with assigned workers**

- [ ] **Step 2: Note current worker energy/health values on the worker screen**

- [ ] **Step 3: Advance one day (click Next Day)**

- [ ] **Step 4: Check `game/log.txt` for correct ordering**

Expected log order:
1. `"Manager auto-rest processing completed"` — pre-events
2. No `HEALTH REGEN` or `ENERGY REGEN` lines before events
3. Daily event processing logs (earnings, outcomes)
4. `HEALTH REGEN` / `ENERGY REGEN` lines — now after events
5. Daily report shown

- [ ] **Step 5: Verify worker energy on worker screen matches post-regen values from log**

The energy shown should be: (energy after event drain) + (regen amount), NOT (energy + regen) - (event drain).
