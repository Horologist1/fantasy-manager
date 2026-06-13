# Nuphar Slime Worker + Reform/Skill-Cap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Nuphar (a unique NSFW slime monster worker) plus a generic capturable slime, a `Slime` race trait whose carriers reform from death instead of dying and have a hard Clever cap, and the `Reforming` debuff that models the cost.

**Architecture:** Data-driven. Two new traits and two new workers are JSON. Two small code changes in Ren'Py `init python`: (a) a `get_skill_cap` helper wired into the existing central skill-write helpers `modify_base_skill`/`set_base_skill`; (b) a `worker_can_reform` helper and a branch in `check_worker_health` that reforms slimes. No new capture event — Nuphar/slime ride the existing Monster Taming loot pool exactly like Amanita.

**Tech Stack:** Ren'Py 8 (Python in `init python:` blocks), JSON data files. Spec: `docs/superpowers/specs/2026-06-13-nuphar-slime-reform-design.md`.

---

## Testing approach (read first)

This project has **no automated test harness** (per `AGENTS.md`: no repo-wide test/lint command). Verification uses what's actually available:

- **JSON syntax:** `python -m json.tool <file>` (errors on invalid JSON).
- **JSON content:** a small script `tools/validate_nuphar_slime.py` written in Task 1 that asserts the data is correct. Run with `python tools/validate_nuphar_slime.py`. It exits non-zero on failure. This is the closest thing to a unit test here and is the TDD spine for the data layer — it's written FIRST (fails), then made to pass task by task.
- **Ren'Py logic:** verified **in-game via the console** (Shift+O). Before any in-game test, clear caches per dev rules: delete `game/cache/*.rpyb` and `game/scripts/**/*.rpyc`, then launch. Exact console commands are given in each code task.

> **Ren'Py/`LA_BIBLIA` rules to honor in all code:** never `isinstance(x, dict/list)` — use `hasattr(x, "get")` / duck-typing; always `.get()` with defaults; data is RevertableDict/List.

---

## File Structure

- `game/data/traits/traits_races.json` — **modify**: add `Slime` race trait.
- `game/data/traits/traits_core.json` — **modify**: add `Reforming` debuff trait (next to `Scarred`).
- `game/data/workers/workers_nsfw_unique.json` — **modify**: add unique `Nuphar`.
- `game/data/workers/workers_nsfw_other.json` — **modify**: add generic `Slime` template.
- `game/scripts/workers/worker_traits.rpy` — **modify**: add `get_skill_cap` (next to `get_attribute_cap`).
- `game/scripts/workers/worker_stats.rpy` — **modify**: `modify_base_skill`/`set_base_skill` honor `get_skill_cap`.
- `game/scripts/script.rpy` — **modify**: item-effect skill fallback honors cap; `check_worker_health` reform branch.
- `game/scripts/workers/worker_management.rpy` — **modify**: add `worker_can_reform` (next to `is_worker_dead`).
- `tools/validate_nuphar_slime.py` — **create**: data validation script.
- `game/images/workers/nuphar/rgthree.compare._temp_gicaa_00046_.png` — **delete**: junk file.

---

### Task 1: Data validation script (the TDD spine)

**Files:**
- Create: `tools/validate_nuphar_slime.py`

- [ ] **Step 1: Write the validation script**

Create `tools/validate_nuphar_slime.py`:

```python
"""Validates the Nuphar / Slime data additions. Run from repo root: python tools/validate_nuphar_slime.py
Exits 0 if all checks pass, 1 otherwise. Safe to run after each data task to watch checks turn green."""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return json.load(f)

def find(items, name):
    return next((x for x in items if x.get("name") == name), None)

errors = []
def check(cond, msg):
    if not cond:
        errors.append(msg)

# --- Slime race trait ---
races = load("game/data/traits/traits_races.json")
slime = find(races, "Slime")
check(slime is not None, "Slime trait missing from traits_races.json")
if slime:
    check(slime.get("reform_on_death") is True, "Slime.reform_on_death must be true")
    check(slime.get("skill_caps", {}).get("Clever") == 50, "Slime.skill_caps.Clever must be 50")
    check(slime.get("nsfw") is True, "Slime.nsfw must be true")
    for race in ("Human", "Elf", "Demon"):
        check(race in slime.get("conflicts", []), f"Slime should conflict with {race}")

# --- Reforming debuff trait ---
core = load("game/data/traits/traits_core.json")
reforming = find(core, "Reforming")
check(reforming is not None, "Reforming trait missing from traits_core.json")
if reforming:
    check(reforming.get("duration") == 3, "Reforming.duration must be 3")
    check(reforming.get("modifiers", {}).get("earnings_multiplier") == 0.5, "Reforming earnings_multiplier must be 0.5")
    sm = reforming.get("modifiers", {}).get("skill_modifiers", {})
    check(all(sm.get(s) == -20 for s in ("Sex", "Combat", "Charm", "Agility")), "Reforming should give -20 to skills")

# --- Nuphar (unique) ---
uniq = load("game/data/workers/workers_nsfw_unique.json")
nuphar = find(uniq, "Nuphar")
check(nuphar is not None, "Nuphar missing from workers_nsfw_unique.json")
if nuphar:
    check(nuphar.get("unique") is True, "Nuphar.unique must be true")
    check(nuphar.get("monster") is True, "Nuphar.monster must be true")
    check(nuphar.get("encounter_only") is True, "Nuphar.encounter_only must be true")
    check(nuphar.get("nsfw") is True, "Nuphar.nsfw must be true")
    check("names_list" not in nuphar, "Nuphar must NOT have names_list (keeps her name)")
    check(nuphar.get("folder") == "nuphar", "Nuphar.folder must be 'nuphar'")
    check(nuphar.get("traits") == ["Slime"], "Nuphar.traits must be ['Slime']")
    check(nuphar.get("skills", {}).get("Clever") == 16, "Nuphar.Clever must be 16 (lowest in game)")

# --- Generic Slime template ---
other = load("game/data/workers/workers_nsfw_other.json")
gslime = find(other, "Slime")
check(gslime is not None, "Generic Slime template missing from workers_nsfw_other.json")
if gslime:
    check(gslime.get("unique") is False, "Generic Slime.unique must be false")
    check(gslime.get("monster") is True, "Generic Slime.monster must be true")
    check(gslime.get("encounter_only") is True, "Generic Slime.encounter_only must be true")
    check(gslime.get("names_list") == "fantasy_female", "Generic Slime needs names_list 'fantasy_female'")
    check(gslime.get("folder") == "nuphar", "Generic Slime.folder must be 'nuphar' (reuse art)")
    check(gslime.get("traits") == ["Slime"], "Generic Slime.traits must be ['Slime']")
    # worse than Nuphar in every skill they share
    if nuphar:
        for k, v in gslime.get("skills", {}).items():
            nv = nuphar.get("skills", {}).get(k)
            if nv is not None:
                check(v < nv, f"Generic Slime.{k} ({v}) must be worse than Nuphar ({nv})")

if errors:
    print("FAIL:")
    for e in errors:
        print("  -", e)
    sys.exit(1)
print("All Nuphar/Slime data checks passed.")
```

- [ ] **Step 2: Run it to confirm it fails (nothing added yet)**

Run: `python tools/validate_nuphar_slime.py`
Expected: `FAIL:` followed by missing-Slime/Reforming/Nuphar/generic-Slime errors, exit code 1.

- [ ] **Step 3: Commit**

```bash
git add tools/validate_nuphar_slime.py
git commit -m "test: add Nuphar/Slime data validation script"
```

---

### Task 2: `Slime` race trait

**Files:**
- Modify: `game/data/traits/traits_races.json`

- [ ] **Step 1: Add the Slime trait**

Append this object as a new element of the top-level array in `game/data/traits/traits_races.json` (add a comma after the previous last object):

```json
{
  "name": "Slime",
  "conflicts": ["Human", "Elf", "Dwarf", "Orc", "Ogre", "Demon", "Angel", "Goblin", "Furry", "Transformed"],
  "modifiers": {
    "skill_modifiers": { "Agility": 5, "Hand": 3, "Extreme": 3 },
    "health": 10,
    "health_regeneration": 1,
    "joy": 15,
    "rebelliousness": -10
  },
  "reform_on_death": true,
  "skill_caps": { "Clever": 50 },
  "nsfw": true,
  "description": "Una criatura gelatinosa: su cuerpo fluido encaja en cualquier forma, pero su mente apenas cuaja. Difícil de destruir de verdad - si la deshacen, vuelve a juntarse de un charco.",
  "attribute_caps": {},
  "daily_effects": {},
  "gender_restriction": null,
  "requires_traits": [],
  "attribute_minimums": {},
  "duration": 0,
  "on_expire": {},
  "only_assigned": false
}
```

- [ ] **Step 2: Validate JSON syntax**

Run: `python -m json.tool game/data/traits/traits_races.json`
Expected: prints the formatted JSON, no error.

- [ ] **Step 3: Run the data validator (Slime checks now pass)**

Run: `python tools/validate_nuphar_slime.py`
Expected: still `FAIL`, but the `Slime trait missing` / `Slime.reform_on_death` / `Slime.skill_caps` lines are GONE. Remaining failures are about Reforming/Nuphar/generic Slime.

- [ ] **Step 4: Commit**

```bash
git add game/data/traits/traits_races.json
git commit -m "feat: add Slime race trait (reform_on_death, Clever cap 50)"
```

---

### Task 3: `Reforming` debuff trait

**Files:**
- Modify: `game/data/traits/traits_core.json`

- [ ] **Step 1: Add the Reforming trait next to Scarred**

In `game/data/traits/traits_core.json`, add this object as a new array element (e.g., right after the `Scarred` object at line ~417; add a comma between objects):

```json
{
  "name": "Reforming",
  "conflicts": [],
  "modifiers": {
    "earnings_multiplier": 0.5,
    "skill_modifiers": {
      "Sex": -20, "Anal": -20, "BDSM": -20, "Hand": -20, "Oral": -20, "Homo": -20,
      "Special": -20, "Group": -20, "Extreme": -20, "Striptease": -20,
      "Combat": -20, "Clever": -20, "Charm": -20, "Service": -20, "Agility": -20, "Craft": -20
    }
  },
  "description": "Aún se está recomponiendo tras deshacerse. Lenta, blanda y de bajo rendimiento hasta que vuelve a cuajar.",
  "attribute_caps": {},
  "daily_effects": {},
  "gender_restriction": null,
  "requires_traits": [],
  "attribute_minimums": {},
  "duration": 3,
  "on_expire": {},
  "only_assigned": false
}
```

- [ ] **Step 2: Validate JSON syntax**

Run: `python -m json.tool game/data/traits/traits_core.json`
Expected: formatted JSON, no error.

- [ ] **Step 3: Run the data validator (Reforming checks now pass)**

Run: `python tools/validate_nuphar_slime.py`
Expected: `Reforming` failures gone; only Nuphar/generic-Slime failures remain.

- [ ] **Step 4: Commit**

```bash
git add game/data/traits/traits_core.json
git commit -m "feat: add Reforming debuff trait (-50% earnings, -20 skills, 3 days)"
```

---

### Task 4: `get_skill_cap` helper

**Files:**
- Modify: `game/scripts/workers/worker_traits.rpy` (add after `get_attribute_cap`, which ends ~line 554)

- [ ] **Step 1: Add the helper**

Insert this function immediately after the `get_attribute_cap` function in `game/scripts/workers/worker_traits.rpy` (same indentation as `get_attribute_cap`, inside the same `init python` block):

```python
    def get_skill_cap(worker, skill_name):
        """Return the max for a base skill given the worker's traits. Defaults to SKILL_MAX.
        A trait may declare {"skill_caps": {"Clever": 50}}. Most restrictive cap wins."""
        cap = None
        for trait_name in (worker.get("traits") or []):
            trait_def = next((t for t in traits_list if t["name"] == trait_name), None)
            if not trait_def:
                trait_def = get_trait_definition(trait_name)  # NSFW/event-assigned traits live in the raw cache
            if not trait_def:
                continue
            caps = trait_def.get("skill_caps", {})
            if hasattr(caps, "get") and skill_name in caps:
                trait_cap = caps[skill_name]
                if cap is None or trait_cap < cap:
                    cap = trait_cap
        return SKILL_MAX if cap is None else min(SKILL_MAX, cap)
```

- [ ] **Step 2: Verify it parses (compile the project)**

Clear caches, then launch the game once so Ren'Py recompiles. From repo root in PowerShell:

```
Remove-Item game/cache/*.rpyb -Force -ErrorAction SilentlyContinue
Get-ChildItem game/scripts -Recurse -Filter *.rpyc | Remove-Item -Force
```

Then launch the game (Ren'Py launcher or `renpy.exe . `). Expected: no compile error referencing `worker_traits.rpy` / `get_skill_cap`.

- [ ] **Step 3: Commit**

```bash
git add game/scripts/workers/worker_traits.rpy
git commit -m "feat: add get_skill_cap (per-trait skill ceiling, default SKILL_MAX)"
```

---

### Task 5: Wire the skill cap into the central skill writers

**Files:**
- Modify: `game/scripts/workers/worker_stats.rpy:517-530`
- Modify: `game/scripts/script.rpy:1887` (item-effect inline fallback)

All skill INCREASES funnel through `modify_base_skill` (level-up `script.rpy:2841`, events `script.rpy:5728`, items `script.rpy:1884`). Capping these two helpers covers every path; the inline fallback at `script.rpy:1887` is the only exception-path that bypasses them.

- [ ] **Step 1: Make `modify_base_skill` / `set_base_skill` honor the cap**

In `game/scripts/workers/worker_stats.rpy`, replace lines 517-530 with:

```python
    def modify_base_skill(worker, skill_name, change):
        """Modify a base skill, clamped to the worker's per-trait cap (default SKILL_MAX)."""
        current = worker["skills"].get(skill_name, 0)
        cap = get_skill_cap(worker, skill_name)
        new_value = max(0, min(cap, current + change))
        worker["skills"][skill_name] = new_value
        renpy.log(f"Modified {skill_name} for {worker.get('name', 'Unknown')}: {current} -> {new_value} (change: {change}, cap: {cap})")
        return new_value

    def set_base_skill(worker, skill_name, value):
        """Set a base skill, clamped to the worker's per-trait cap (default SKILL_MAX)."""
        cap = get_skill_cap(worker, skill_name)
        capped_value = max(0, min(cap, value))
        worker["skills"][skill_name] = capped_value
        renpy.log(f"Set {skill_name} for {worker.get('name', 'Unknown')} to {capped_value} (requested: {value}, cap: {cap})")
        return capped_value
```

- [ ] **Step 2: Make the item-effect fallback honor the cap**

In `game/scripts/script.rpy`, line 1887, replace:

```python
                                worker.setdefault("skills", {})[skill_name] = max(0, min(SKILL_MAX, current + int(delta)))
```

with:

```python
                                worker.setdefault("skills", {})[skill_name] = max(0, min(get_skill_cap(worker, skill_name), current + int(delta)))
```

- [ ] **Step 3: Verify in-game console**

Clear caches (commands from Task 4 Step 2) and launch. Open console (Shift+O) and run:

```python
nuph = next((w for w in workers if w.get("name") == "Nuphar"), None) or [w for w in workers][0]
for _ in range(40): modify_base_skill(nuph, "Clever", 5)
print("Clever:", nuph["skills"]["Clever"])     # expect 50 (capped)
for _ in range(40): modify_base_skill(nuph, "Sex", 5)
print("Sex:", nuph["skills"]["Sex"])            # expect 100 (no cap on Sex)
```

Expected: `Clever: 50` and `Sex: 100`. (If no Nuphar in roster yet, run this after Task 7 instead, or test on any worker after giving it the Slime trait.)

- [ ] **Step 4: Commit**

```bash
git add game/scripts/workers/worker_stats.rpy game/scripts/script.rpy
git commit -m "feat: enforce per-trait skill caps in base-skill writers"
```

---

### Task 6: `worker_can_reform` helper

**Files:**
- Modify: `game/scripts/workers/worker_management.rpy` (add next to `is_worker_dead`, ~line 80)

- [ ] **Step 1: Add the helper**

Insert this function in the same `init python` block as `is_worker_dead` in `game/scripts/workers/worker_management.rpy`:

```python
    def worker_can_reform(worker):
        """True if any of the worker's traits declares reform_on_death (e.g. the Slime race)."""
        if worker is None:
            return False
        for trait_name in (worker.get("traits") or []):
            trait_def = next((t for t in traits_list if t["name"] == trait_name), None)
            if not trait_def:
                trait_def = get_trait_definition(trait_name)
            if trait_def and trait_def.get("reform_on_death"):
                return True
        return False
```

- [ ] **Step 2: Verify it parses**

Clear caches and launch (commands from Task 4 Step 2). Expected: no compile error.

- [ ] **Step 3: Commit**

```bash
git add game/scripts/workers/worker_management.rpy
git commit -m "feat: add worker_can_reform helper"
```

---

### Task 7: Reform branch in `check_worker_health`

**Files:**
- Modify: `game/scripts/script.rpy:4092-4105`

- [ ] **Step 1: Add the reform branch**

In `game/scripts/script.rpy`, replace the body of `check_worker_health` (lines 4092-4105) with:

```python
    def check_worker_health():
        global workers
        to_remove = []
        dead_names = []
        for worker in workers:
            if worker["health"] <= 0:
                # Slimes reform from a puddle instead of dying - but only if not already mid-reform.
                already_reforming = "Reforming" in (worker.get("traits") or [])
                if worker_can_reform(worker) and not already_reforming:
                    worker["health"] = max(1, calculate_max_health(worker) // 4)
                    add_trait_with_duration(worker, "Reforming", 3)
                    renpy.notify(f"{worker['name']} reformed from a puddle!")
                    renpy.log(f"{worker['name']} reformed instead of dying (health -> {worker['health']})")
                    continue
                unassign_worker(worker)
                to_remove.append(worker)
                dead_names.append(worker["name"])
                # Add the worker to the dead workers list
                add_to_dead_workers(worker["name"])
        for worker in to_remove:
            workers.remove(worker)
        return dead_names  # Return list of names instead of count
```

- [ ] **Step 2: Verify in-game console — first death reforms**

Clear caches, launch, open console (Shift+O). Use any slime-trait worker (give one the trait if none captured yet):

```python
w = next((x for x in workers if "Slime" in (x.get("traits") or [])), None)
if w is None:
    w = workers[0]; w["traits"] = ["Slime"]      # temp for testing
w["health"] = 0
check_worker_health()
print("alive:", w in workers, "health:", w["health"], "traits:", list(w["traits"]))
```

Expected: `alive: True`, `health:` a positive number (~25% of max), `traits:` includes `Reforming`. A "reformed from a puddle" notification appears.

- [ ] **Step 3: Verify in-game console — second death (while Reforming) is real death**

Continuing in the same console session (w now has Reforming):

```python
w["health"] = 0
check_worker_health()
print("alive:", w in workers, "dead-listed:", is_worker_dead(w["name"]))
```

Expected: `alive: False`, `dead-listed: True`.

- [ ] **Step 4: Commit**

```bash
git add game/scripts/script.rpy
git commit -m "feat: slimes reform from death once; die for real if killed mid-reform"
```

---

### Task 8: Nuphar (unique) + generic Slime workers

**Files:**
- Modify: `game/data/workers/workers_nsfw_unique.json`
- Modify: `game/data/workers/workers_nsfw_other.json`

- [ ] **Step 1: Add Nuphar to the unique array**

Append to the top-level array in `game/data/workers/workers_nsfw_unique.json` (comma after previous last object):

```json
{
  "name": "Nuphar",
  "folder": "nuphar",
  "cost": 1500,
  "nsfw": true,
  "unique": true,
  "encounter_only": true,
  "monster": true,
  "procedural": false,
  "skills": {
    "Sex": 45, "Anal": 38, "BDSM": 25, "Hand": 44, "Oral": 42, "Homo": 30,
    "Special": 40, "Group": 40, "Extreme": 43, "Striptease": 33,
    "Combat": 32, "Clever": 16, "Charm": 28, "Service": 16, "Agility": 48, "Craft": 10,
    "Specialty 4": 24, "Specialty 5": 22, "Specialty 6": 26, "Specialty 7": 20,
    "Specialty 8": 24, "Specialty 9": 28, "Specialty 10": 22, "Specialty 11": 20, "Specialty 12": 24
  },
  "traits": ["Slime"],
  "description": "Una slime girl de cuerpo translúcido y mente simple. Lo que le falta de seso le sobra de aguante: por mucho que la deshagan, siempre vuelve a juntarse.",
  "gender": "female",
  "comfort_desired": 1
}
```

- [ ] **Step 2: Add the generic Slime template to the other array**

Append to the top-level array in `game/data/workers/workers_nsfw_other.json` (comma after previous last object):

```json
{
  "name": "Slime",
  "folder": "nuphar",
  "cost": 1100,
  "nsfw": true,
  "unique": false,
  "encounter_only": true,
  "monster": true,
  "procedural": false,
  "skills": {
    "Sex": 37, "Anal": 30, "BDSM": 17, "Hand": 36, "Oral": 34, "Homo": 22,
    "Special": 32, "Group": 32, "Extreme": 35, "Striptease": 25,
    "Combat": 24, "Clever": 14, "Charm": 20, "Service": 12, "Agility": 40, "Craft": 8,
    "Specialty 4": 16, "Specialty 5": 14, "Specialty 6": 18, "Specialty 7": 12,
    "Specialty 8": 16, "Specialty 9": 20, "Specialty 10": 14, "Specialty 11": 12, "Specialty 12": 16
  },
  "names_list": "fantasy_female",
  "traits": ["Slime"],
  "description": "Una slime salvaje capturada de las ciénagas: dócil, simple y prácticamente indestructible.",
  "gender": "female",
  "comfort_desired": 1
}
```

- [ ] **Step 3: Validate JSON syntax (both files)**

Run:
```
python -m json.tool game/data/workers/workers_nsfw_unique.json
python -m json.tool game/data/workers/workers_nsfw_other.json
```
Expected: formatted JSON, no error.

- [ ] **Step 4: Run the full data validator (everything passes now)**

Run: `python tools/validate_nuphar_slime.py`
Expected: `All Nuphar/Slime data checks passed.` exit 0.

- [ ] **Step 5: Commit**

```bash
git add game/data/workers/workers_nsfw_unique.json game/data/workers/workers_nsfw_other.json
git commit -m "feat: add Nuphar (unique slime) and generic Slime capture template"
```

---

### Task 9: Delete junk image + capture smoke test

**Files:**
- Delete: `game/images/workers/nuphar/rgthree.compare._temp_gicaa_00046_.png`

- [ ] **Step 1: Delete the junk file**

```
Remove-Item "game/images/workers/nuphar/rgthree.compare._temp_gicaa_00046_.png" -Force
```

- [ ] **Step 2: In-game capture smoke test**

Clear caches, launch, open console (Shift+O):

```python
nuph = loot_monster_worker({"name": "Nuphar"})
print("Nuphar:", nuph and nuph["name"], "folder:", nuph and nuph["folder"], "traits:", nuph and list(nuph["traits"]))
gen = loot_monster_worker({"monster": True, "encounter_only": True})
print("generic capture:", gen and gen["name"], "folder:", gen and gen["folder"])
```

Expected: Nuphar returns name `Nuphar`, folder `nuphar`, traits `['Slime']`. The generic capture returns some monster (possibly a renamed Slime) with a valid folder. No exceptions.

- [ ] **Step 3: Verify profile art resolves**

In the running game, capture or add Nuphar to the roster and open her Worker Details. Expected: her profile image shows (art from `game/images/workers/nuphar/`), no missing-image placeholder.

- [ ] **Step 4: Commit**

```bash
git add -A game/images/workers/nuphar
git commit -m "chore: remove ComfyUI temp file from Nuphar art folder"
```

---

### Task 10: Final integration verification + merge to main

- [ ] **Step 1: Full data validation**

Run: `python tools/validate_nuphar_slime.py`
Expected: `All Nuphar/Slime data checks passed.`

- [ ] **Step 2: End-to-end in-game checklist** (cache cleared, NSFW enabled)

1. Capture Nuphar (console: add `loot_monster_worker({"name":"Nuphar"})` result to `workers`); she keeps name "Nuphar", art shows.
2. Train her Clever past 50 → stops at 50; train Sex → reaches 100.
3. Set her `health = 0`, run `check_worker_health()` → she reforms (~25% HP, gains `Reforming`, "reformed from a puddle" notify, still in roster).
4. Advance 3 days → `Reforming` expires and is removed from her traits.
5. While `Reforming` is active, set `health = 0` + `check_worker_health()` → she dies for real (`is_worker_dead("Nuphar")` is True).
6. Capture a generic slime (`loot_monster_worker({"monster":True,"encounter_only":True})` repeatedly) → a `Slime`-trait worker with a random `fantasy_female` name and `nuphar` folder appears.

- [ ] **Step 3: Confirm only Nuphar/slime files are staged for main**

The working branch may carry unrelated changes (devkit, stray PNGs, `script.rpy` devkit edits). Verify the merge to `main` includes ONLY this feature's files:

```
game/data/traits/traits_races.json
game/data/traits/traits_core.json
game/data/workers/workers_nsfw_unique.json
game/data/workers/workers_nsfw_other.json
game/scripts/workers/worker_traits.rpy
game/scripts/workers/worker_stats.rpy
game/scripts/workers/worker_management.rpy
game/scripts/script.rpy   (ONLY the get_skill_cap fallback + check_worker_health changes — NOT unrelated devkit edits)
tools/validate_nuphar_slime.py
docs/superpowers/specs/2026-06-13-nuphar-slime-reform-design.md
docs/superpowers/plans/2026-06-13-nuphar-slime-reform.md
game/images/workers/nuphar/  (deletion of the temp PNG)
```

> `script.rpy` is the risk: it already had unrelated modifications before this work. When landing on `main`, stage only the Nuphar-related hunks (`git add -p game/scripts/script.rpy`) so devkit edits don't ride along. Coordinate with the user on whether the pre-existing `script.rpy`/PNG changes should go too.

- [ ] **Step 4: Land on main** (per user: commit everything to `main` at the end)

Confirm the exact mechanism with the user first (the feature was built on `feature/devkit-web`). Likely: create commits on `main` containing only the files above. Do not force-push; do not bundle unrelated devkit work.

---

## Self-Review notes

- **Spec coverage:** Slime trait (Task 2), Reforming (Task 3), skill-cap feature (Tasks 4-5), reform logic (Tasks 6-7), Nuphar + generic Slime (Task 8), cleanup (Task 9), capture-as-Amanita (verified Task 9/10), Clever=16 (validator + Task 8). All spec sections mapped.
- **Simplification vs spec:** spec said "reroute 3 clamp sites"; investigation showed events/items/level-up already call `modify_base_skill`, so only the two helpers (+ one item fallback line) need changing. `worker_training.rpy:853` is difficulty math, not a skill write — left untouched. This is noted in Task 5.
- **Out of scope (unchanged):** broken `monsters` folder in `spawn_new_monster_worker` (never reached for slimes); guaranteed "Nuphar first"; dedicated capture event.
- **Type consistency:** `get_skill_cap(worker, skill_name)`, `worker_can_reform(worker)`, `modify_base_skill`/`set_base_skill` signatures consistent across tasks; trait names `Slime`/`Reforming` and field names `reform_on_death`/`skill_caps` consistent between JSON and code.
