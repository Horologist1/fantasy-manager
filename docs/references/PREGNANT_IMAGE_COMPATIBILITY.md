# Pregnant Image Compatibility Analysis

## Current Situation

### Whoremaster (WM)
- Uses **"Preg"** prefix in image filenames
- Examples: `Preg (2).jpg`, `PregSex.png`, `PregGroup.jpeg`, `PregNude.jpeg`

### Fantasy Manager (FM)
- Uses **"Pregnant"** trait to identify images
- Searches for **"pregnant_"** prefix in filenames
- Example: `pregnant_sex.jpg`, `pregnant_profile.png`

## Problem

**No compatibility exists between "Preg" and "pregnant"**

When FM searches for images with the "Pregnant" trait:
- It looks for: `pregnant_*` files
- WM has: `Preg*` files
- **Result: Images are not found**

## Current FM Search System

FM uses `get_trait_prefixes()` which generates:
- `"pregnant"` → searches for `pregnant_*` files

The search is case-insensitive (uses `.lower()`), but the prefix must match exactly:
- `pregnant_` matches `pregnant_sex.jpg` ✅
- `pregnant_` does NOT match `preg_sex.jpg` ❌
- `pregnant_` does NOT match `PregSex.jpg` ❌

## Solutions

### Option 1: Expand Trait Prefix Search (Recommended)
Modify `get_trait_prefixes()` to return multiple search patterns for "Pregnant":
- `["pregnant", "preg", "preggo"]`

This way FM will search for:
- `pregnant_*`
- `preg_*` or files starting with `Preg`
- `preggo_*` or files starting with `Preggo`

**Pros:**
- No need to rename existing WM images
- Backward compatible with FM's current naming
- Works with both naming conventions

**Cons:**
- Slightly more complex search logic

### Option 2: Rename WM Images
Update `rename_wm_images.py` to rename:
- `Preg` → `pregnant`
- `PregSex` → `pregnant_sex`
- `PregGroup` → `pregnant_group`
- etc.

**Pros:**
- Simple, direct solution
- Standardizes naming

**Cons:**
- Requires renaming all WM images
- May break if WM images are updated

### Option 3: Hybrid Approach
- Expand trait search to include "preg" and "preggo"
- Optionally rename during import for consistency

## Recommendation

**Option 1** is recommended because:
1. It's backward compatible
2. No manual renaming needed
3. Works with both WM and FM naming conventions
4. Similar to how FM already handles skill name variations (e.g., "homo" → ["les", "gay"])

## Implementation ✅ COMPLETED

### Changes Made:

1. **Modified `get_trait_prefixes()` in `event_visuals.rpy`:**
   - Now returns multiple variants for "Pregnant": `["pregnant", "preg", "preggo"]`
   - Includes variants in all trait combinations
   - Maintains priority order

2. **Enhanced `get_pattern_matches_flexible()`:**
   - Now searches for patterns with and without underscores
   - Handles WM camelCase naming: "PregSex" matches "preg_sex" pattern
   - Case-insensitive matching

### How It Works Now:

When a worker has the "Pregnant" trait, FM will search for:
- `pregnant_*` (FM standard)
- `preg_*` (WM standard with underscore)
- `preggo_*` (Alternative)
- `Preg*` (WM camelCase, no underscore) - via pattern matching

**Examples:**
- `PregSex.jpg` → Found when searching for "preg_sex" ✅
- `Preg (2).jpg` → Found when searching for "preg" ✅
- `PregGroup.jpeg` → Found when searching for "preg_group" ✅
- `pregnant_sex.jpg` → Found when searching for "pregnant_sex" ✅

### Optional Renaming

The `rename_wm_images.py` script has commented mappings for renaming "Preg" → "pregnant" if you want to standardize naming. However, this is **not necessary** as FM now supports both conventions.

