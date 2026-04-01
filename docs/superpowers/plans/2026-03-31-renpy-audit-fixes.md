# Ren'Py Fantasy Manager: Bug & Optimization Audit Fix Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the three highest-impact categories found in the codebase audit: the `isinstance(x, dict)` anti-pattern (68+ instances, causes silent failures with Ren'Py's RevertableDict), uncached `load_interactions()` (reparses JSON on every screen render), and redundant `renpy.list_files()` calls (multiple uncoordinated filesystem scans at init and runtime).

**Architecture:** Three independent fix tracks that can be executed in parallel. Track A replaces isinstance dict checks with `hasattr(x, "get")` per the project's own coding standard (docs/LA_BIBLIA_DE_LO_QUE_NUNCA_SE_DEBE_HACER.md). Track B adds a module-level cache to `load_interactions()` and fixes a double file-open bug. Track C consolidates all `renpy.list_files()` calls behind a shared cache.

**Tech Stack:** Ren'Py (Python 2/3 compatible), JSON data files, RPY scripts.

**What passed audit (no fixes needed):** JSON data integrity across all 5 trait files, 7 event files, items, buildings, and interactions. All 163 traits consistent, all cross-references valid, all conflicts symmetric.

---

## File Map

| Track | Files to Modify | Responsibility |
|-------|----------------|----------------|
| **A: isinstance fix** | `game/scripts/workers/worker_traits.rpy`, `game/scripts/workers/worker_defaults.rpy`, `game/scripts/save_snapshot.rpy`, `game/scripts/script.rpy`, `game/scripts/events/event_daily_exec.rpy`, `game/scripts/events/event_resolution.rpy`, `game/scripts/events/events_logic.rpy`, `game/scripts/core/screens.rpy`, `game/scripts/buildings/building_logic.rpy`, `game/scripts/main_flow.rpy`, `game/scripts/tutorial_system.rpy` | Replace `isinstance(x, dict)` with `hasattr(x, "get")` |
| **B: Interaction cache** | `game/scripts/workers/worker_interactions.rpy` | Cache load_interactions(), fix double file-open |
| **C: File list cache** | `game/scripts/script.rpy`, `game/scripts/workers/worker_interactions.rpy`, `game/scripts/workers/worker_traits.rpy`, `game/scripts/events/events_logic.rpy` | Consolidate renpy.list_files() behind shared cache |

---

## Track A: Fix isinstance(x, dict) Anti-Pattern

The project's own coding bible (`docs/LA_BIBLIA_DE_LO_QUE_NUNCA_SE_DEBE_HACER.md`) bans `isinstance(x, dict)` because Ren'Py uses `RevertableDict` which fails that check. The fix is mechanical: replace with `hasattr(x, "get")` (for "is this dict-like?") or remove the check entirely when unnecessary.

### Task A1: worker_traits.rpy isinstance fixes

**Files:**
- Modify: `game/scripts/workers/worker_traits.rpy`

- [ ] **Step 1: Fix line ~136 in `get_all_traits()`**

Replace:
```python
if isinstance(cached, dict) and cached:
```
With:
```python
if cached and hasattr(cached, "get"):
```

- [ ] **Step 2: Fix line ~181 in conflict check**

Replace:
```python
existing_def = cache.get(existing_name) if isinstance(cache, dict) else None
```
With:
```python
existing_def = cache.get(existing_name) if hasattr(cache, "get") else None
```

- [ ] **Step 3: Fix line ~565 in `ensure_minimum_traits()`**

Replace:
```python
if isinstance(cache, dict) and cache:
```
With:
```python
if cache and hasattr(cache, "get"):
```

- [ ] **Step 4: Verify by searching file for remaining isinstance(*, dict)**

Run: Search the file for `isinstance` and verify no dict checks remain.

- [ ] **Step 5: Commit**

```bash
git add game/scripts/workers/worker_traits.rpy
git commit -m "fix: replace isinstance(x, dict) with hasattr checks in worker_traits"
```

### Task A2: worker_defaults.rpy isinstance fix

**Files:**
- Modify: `game/scripts/workers/worker_defaults.rpy`

- [ ] **Step 1: Fix line ~172**

Replace:
```python
known_trait_names = set(t.get("name") for t in trait_catalog if isinstance(t, dict) and t.get("name"))
```
With:
```python
known_trait_names = set(t.get("name") for t in trait_catalog if hasattr(t, "get") and t.get("name"))
```

- [ ] **Step 2: Commit**

```bash
git add game/scripts/workers/worker_defaults.rpy
git commit -m "fix: replace isinstance(x, dict) with hasattr check in worker_defaults"
```

### Task A3: save_snapshot.rpy isinstance fixes (16 instances)

**Files:**
- Modify: `game/scripts/save_snapshot.rpy`

- [ ] **Step 1: Global replace isinstance(*, dict) with hasattr pattern**

Search for all occurrences of `isinstance(` combined with `dict)` in the file. For each one:

Pattern `isinstance(x, dict)` becomes `hasattr(x, "get")`.

Key lines to fix:
- Line ~85, ~125, ~140, ~144, ~157, ~172, ~224, ~247, ~279, ~498, ~509, ~545, ~1071, ~1332, ~1338, ~1355

Critical fixes:
```python
# Line ~140: Worker name lookup
# OLD:
name_to_worker = {w.get("name"): w for w in store.workers if isinstance(w, dict) and w.get("name")}
# NEW:
name_to_worker = {w.get("name"): w for w in store.workers if hasattr(w, "get") and w.get("name")}

# Line ~157: Building servant check
# OLD:
if isinstance(servant, dict):
# NEW:
if hasattr(servant, "get"):

# Line ~1355: Building total
# OLD:
total = sum(len(b.get("assigned_servants", [])) for b in store.available_buildings.values() if isinstance(b, dict))
# NEW:
total = sum(len(b.get("assigned_servants", [])) for b in store.available_buildings.values() if hasattr(b, "get"))
```

- [ ] **Step 2: Verify no isinstance(*, dict) remains**

Search file for `isinstance` and confirm all dict checks are converted.

- [ ] **Step 3: Commit**

```bash
git add game/scripts/save_snapshot.rpy
git commit -m "fix: replace 16 isinstance(x, dict) checks in save_snapshot"
```

### Task A4: script.rpy isinstance fixes (48 instances)

**Files:**
- Modify: `game/scripts/script.rpy`

- [ ] **Step 1: Handle the dual-check workaround pattern**

Some lines already have a workaround:
```python
# OLD (line ~1641):
elif isinstance(effect_raw, dict) or type(effect_raw).__name__ == "dict":
# NEW:
elif hasattr(effect_raw, "get"):
```
The `type().__name__` check was a workaround for the RevertableDict issue. `hasattr(x, "get")` replaces both.

- [ ] **Step 2: Replace all remaining isinstance(*, dict) in script.rpy**

Apply the same `isinstance(x, dict)` -> `hasattr(x, "get")` pattern to all 48 instances. Key areas:
- Lines ~403, ~412: Worker initialization
- Lines ~1616, ~1641, ~1680: Effect processing
- Lines ~2546: Filter logic
- Lines ~2714-2723: Building lookups
- Lines ~3088-3635: Building/worker assignment (20+ instances)

- [ ] **Step 3: Verify and commit**

```bash
git add game/scripts/script.rpy
git commit -m "fix: replace 48 isinstance(x, dict) checks in script.rpy"
```

### Task A5: Event and screen files isinstance fixes

**Files:**
- Modify: `game/scripts/events/event_daily_exec.rpy` (~10 instances)
- Modify: `game/scripts/events/event_resolution.rpy` (~1 instance)
- Modify: `game/scripts/events/events_logic.rpy` (~4 instances)
- Modify: `game/scripts/core/screens.rpy` (~1 instance)
- Modify: `game/scripts/buildings/building_logic.rpy` (if any)
- Modify: `game/scripts/main_flow.rpy` (~1 instance)
- Modify: `game/scripts/tutorial_system.rpy` (~2 instances)

- [ ] **Step 1: Fix event_daily_exec.rpy**

Replace all `isinstance(x, dict)` with `hasattr(x, "get")` at lines ~206, ~445, ~474, ~935, ~1124, ~1131, ~1167, ~1190, ~1199, ~1216, ~1229, ~1430.

- [ ] **Step 2: Fix event_resolution.rpy**

Line ~24:
```python
# OLD:
if isinstance(descriptions, dict):
# NEW:
if hasattr(descriptions, "get"):
```

- [ ] **Step 3: Fix events_logic.rpy**

Lines ~77, ~105, ~111, ~149: same pattern.

- [ ] **Step 4: Fix screens.rpy**

Line ~6367:
```python
# OLD:
$ store.manager_pending_skills = _pending_d if isinstance(_pending_d, dict) else {}
# NEW:
$ store.manager_pending_skills = _pending_d if hasattr(_pending_d, "get") else {}
```

- [ ] **Step 5: Fix main_flow.rpy**

Line ~80:
```python
# OLD:
if event_data and isinstance(event_data, dict):
# NEW:
if event_data and hasattr(event_data, "get"):
```

- [ ] **Step 6: Fix tutorial_system.rpy**

Lines ~175, ~215: same pattern.

- [ ] **Step 7: Commit all remaining files**

```bash
git add game/scripts/events/event_daily_exec.rpy game/scripts/events/event_resolution.rpy game/scripts/events/events_logic.rpy game/scripts/core/screens.rpy game/scripts/main_flow.rpy game/scripts/tutorial_system.rpy
git commit -m "fix: replace isinstance(x, dict) in events, screens, and remaining files"
```

### Task A6: Final isinstance sweep

- [ ] **Step 1: Search entire codebase for remaining isinstance(*, dict)**

```bash
grep -rn "isinstance.*dict" game/scripts/**/*.rpy
```

Any remaining instances should be evaluated: if they genuinely need to check for Python `dict` specifically (rare), add a comment explaining why. Otherwise, convert.

- [ ] **Step 2: Commit any stragglers**

---

## Track B: Cache load_interactions() and Fix Double File-Open

### Task B1: Fix double file-open bug

**Files:**
- Modify: `game/scripts/workers/worker_interactions.rpy:25`

- [ ] **Step 1: Find the double-open pattern**

Current code (approximately):
```python
with renpy.file(file) as f:
    file_content = f.read()
    file_interactions = json.load(renpy.file(file))  # BUG: opens file AGAIN
```

- [ ] **Step 2: Fix to single open**

```python
with renpy.file(file) as f:
    file_content = f.read()
    file_interactions = json.loads(file_content)  # Parse from already-read content
```

Or simpler:
```python
with renpy.file(file) as f:
    file_interactions = json.load(f)
```

- [ ] **Step 3: Commit**

```bash
git add game/scripts/workers/worker_interactions.rpy
git commit -m "fix: remove double file-open in load_interactions"
```

### Task B2: Add persistent cache to load_interactions()

**Files:**
- Modify: `game/scripts/workers/worker_interactions.rpy`

- [ ] **Step 1: Add module-level cache variable**

Near the top of the `init python:` block, add:
```python
_interactions_cache = None
_interactions_cache_nsfw = None  # Track which NSFW mode the cache was built for
```

- [ ] **Step 2: Modify load_interactions() to use cache**

```python
def load_interactions():
    global _interactions_cache, _interactions_cache_nsfw
    current_nsfw = getattr(persistent, "nsfw_enabled", False)
    if _interactions_cache is not None and _interactions_cache_nsfw == current_nsfw:
        return list(_interactions_cache)  # Return copy to prevent mutation

    interactions = []
    # ... existing loading logic (with the double-open fix from B1) ...

    _interactions_cache = interactions
    _interactions_cache_nsfw = current_nsfw
    return list(interactions)
```

- [ ] **Step 3: Add cache invalidation function**

```python
def invalidate_interactions_cache():
    global _interactions_cache, _interactions_cache_nsfw
    _interactions_cache = None
    _interactions_cache_nsfw = None
```

- [ ] **Step 4: Verify callers get fresh data when needed**

Check that NSFW toggle or mod loading invalidates the cache. If the game doesn't hot-reload interactions, no invalidation is needed beyond the NSFW check.

- [ ] **Step 5: Commit**

```bash
git add game/scripts/workers/worker_interactions.rpy
git commit -m "perf: cache load_interactions() to avoid per-frame JSON reload"
```

---

## Track C: Consolidate renpy.list_files() Calls

### Task C1: Create shared file list cache

**Files:**
- Modify: `game/scripts/script.rpy` (init python block)

- [ ] **Step 1: Add a shared file list cache at the start of init python**

```python
init python:
    # Shared file list cache - renpy.list_files() is expensive; call once, reuse everywhere.
    _renpy_file_list_cache = None

    def get_cached_file_list():
        global _renpy_file_list_cache
        if _renpy_file_list_cache is None:
            _renpy_file_list_cache = renpy.list_files()
        return _renpy_file_list_cache

    store.get_cached_file_list = get_cached_file_list
```

- [ ] **Step 2: Replace the 3 calls in script.rpy init**

Replace each `renpy.list_files()` call at lines ~265, ~316, ~342 with `get_cached_file_list()`.

- [ ] **Step 3: Commit**

```bash
git add game/scripts/script.rpy
git commit -m "perf: consolidate renpy.list_files() behind shared cache in script.rpy"
```

### Task C2: Update other modules to use shared cache

**Files:**
- Modify: `game/scripts/workers/worker_interactions.rpy` (line ~14)
- Modify: `game/scripts/workers/worker_traits.rpy` (line ~45)
- Modify: `game/scripts/events/events_logic.rpy` (line ~336)

- [ ] **Step 1: Replace renpy.list_files() in worker_interactions.rpy**

```python
# OLD:
all_files = renpy.list_files()
# NEW:
_gcfl = getattr(store, "get_cached_file_list", None)
all_files = _gcfl() if callable(_gcfl) else renpy.list_files()
```

- [ ] **Step 2: Replace in worker_traits.rpy**

Same pattern at line ~45.

- [ ] **Step 3: Replace in events_logic.rpy**

Same pattern at line ~336.

- [ ] **Step 4: Commit**

```bash
git add game/scripts/workers/worker_interactions.rpy game/scripts/workers/worker_traits.rpy game/scripts/events/events_logic.rpy
git commit -m "perf: use shared file list cache across all modules"
```

### Task C3: Update worker_loader.rpy to use shared cache

**Files:**
- Modify: `game/scripts/workers/worker_loader.rpy`

- [ ] **Step 1: Replace renpy.list_files() in _get_worker_json_files()**

```python
def _get_worker_json_files(refresh=False):
    global _worker_json_files_cache
    if refresh or _worker_json_files_cache is None:
        _gcfl = getattr(store, "get_cached_file_list", None)
        all_files = _gcfl() if callable(_gcfl) else renpy.list_files()
        workers_folder_path = "data/workers"
        _worker_json_files_cache = [
            f for f in all_files
            if f.startswith(workers_folder_path) and f.endswith(".json")
        ]
    return list(_worker_json_files_cache)
```

- [ ] **Step 2: Commit**

```bash
git add game/scripts/workers/worker_loader.rpy
git commit -m "perf: use shared file list cache in worker_loader"
```

---

## Verification

After all tracks are complete:

- [ ] **Launch game and verify**: New Game starts without errors
- [ ] **Load existing save**: Verify save_snapshot.rpy changes don't break save loading
- [ ] **Open Buy Servants**: Workers display correctly (worker_loader + interactions)
- [ ] **Open Worker Details**: Interactions load (cached load_interactions)
- [ ] **Run Training interaction**: Full flow works (worker_training.rpy)
- [ ] **Check Ren'Py console (Shift+O)**: No "isinstance" warnings or type errors in log
- [ ] **Performance check**: Navigate Worker Details / Manager screen several times - should feel snappier with interaction caching
