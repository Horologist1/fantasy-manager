# Compatibility Guide: Whoremaster → Fantasy Manager

## Executive Summary

This document analyzes the compatibility between **Whoremaster 7.2.2** and **Fantasy Manager**, providing a complete mapping of data structures and conversion recommendations.

---

## 📊 Architecture Comparison

### Data Formats

| Aspect | Whoremaster | Fantasy Manager |
|--------|-------------|-----------------|
| **Character Format** | XML (.girlsx, .rgirlsx) | JSON |
| **Item Format** | XML (.itemsx) | JSON |
| **Trait Format** | XML (.traitsx) | JSON |
| **Job Format** | XML | Ren'Py Scripts |
| **Images** | Folder per character | Folder per character |

### Character Structure

#### Whoremaster (`.girlsx` - Unique)
```xml
<Girl Name="Aeris Gainsborough" 
      Charisma="70" Intelligence="60" Agility="30" ...>
    <Trait Name="Cute" />
    <Trait Name="Strong Magic" />
</Girl>
```

#### Whoremaster (`.rgirlsx` - Random/Template)
```xml
<Girl Name="RgirlOrc" Desc="..." Human="No">
    <Stat Name="Charisma" Min="20" Max="70" />
    <Skill Name="Combat" Min="30" Max="50" />
    <Trait Name="Big Boobs" Percent="50" />
</Girl>
```

#### Fantasy Manager (JSON)
```json
{
  "name": "Elena",
  "folder": "iris",
  "cost": 1400,
  "nsfw": true,
  "unique": false,
  "skills": {
    "Sex": 23, "Combat": 40, "Charm": 45, ...
  },
  "traits": ["Human", "Beautiful"],
  "description": "...",
  "gender": "female",
  "comfort_desired": 4
}
```

---

## 🎯 Skill Mapping

### Direct Skills

| Whoremaster | Fantasy Manager | Notes |
|-------------|-----------------|-------|
| Combat | Combat | ✅ Direct |
| Service | Service | ✅ Direct |
| Anal | Anal | ✅ Direct |
| BDSM | BDSM | ✅ Direct |
| Group | Group | ✅ Direct |
| Strip | Striptease | ✅ Renamed |

### Sexual Skills

| Whoremaster | Fantasy Manager | Notes |
|-------------|-----------------|-------|
| NormalSex | Sex | ✅ Main sexual skill |
| OralSex | Oral | ✅ Direct |
| Lesbian | Homo | ✅ Homosexual activities |
| Handjob | Hand | ✅ Direct |
| TittySex | Special | Combined into Special |
| Footjob | Special | Combined into Special |
| Beastiality | Extreme | Mapped to Extreme |

### Non-Sexual Skills

| Whoremaster | Fantasy Manager | Notes |
|-------------|-----------------|-------|
| Magic | Craft | Magical abilities → crafting |
| Medicine | Clever | Medical knowledge → intelligence |
| Performance | Charm | Acting → charisma |
| Crafting | Craft | ✅ Direct |
| Farming | Service | Agricultural work → service |
| Cooking | Service | Cooking → service |
| Herbalism | Craft | Herbalism → crafting |
| Brewing | Clever | Distillation → intelligence |
| AnimalHandling | Craft | Animals → crafting |

### Stats → Skills (Contribution)

| WM Stat | FM Skill | Factor |
|---------|----------|--------|
| Charisma | Charm | 50% |
| Intelligence | Clever | 50% |
| Agility | Agility | 100% |
| Strength | Combat | 30% |
| Constitution | Combat | 20% |
| Confidence | Charm | 30% |
| Beauty | Charm | 20% |
| Libido | Sex | 20% |

### Skill value conversion (WM → FM)

- **Skills specified in Whoremaster** (XML): the converter applies a scale conversion so WM values become FM 0–100.
  - Default: WM scale 0–100 → FM 0–100 (1:1).
  - If your pack uses a different scale (e.g. 0–70), set `WM_SKILL_SCALE_MAX = 70` in the editor/devkit so that WM 70 → FM 100.
- **Skills not present in WM**: they get a baseline in the same range as FM unique workers (main skills 20–30, Specialty 4–12 varied 18–32), so imported characters stay comparable to game workers.

---

## 🏷️ Trait Mapping

### Personality Traits

| Whoremaster | Fantasy Manager |
|-------------|-----------------|
| Agile | Agile |
| Brawler | Brawler |
| Clumsy | Clumsy |
| Delicate | Delicate |
| Strong | Strong |
| Tough | Tough |
| Open Minded | Open Minded |
| Shy | Shy |
| Nervous | Nervous |
| Optimist | Optimist |
| Pessimist | Pessimist |
| Quick Learner | Quick Learner |
| Slow Learner | Slow Learner |
| Sadistic | Sadistic |
| Fearless | Confident |
| Iron Will | Rebellious |
| Broken Will | Obedient |
| Dependant | Dependant |

### Appearance Traits

| Whoremaster | Fantasy Manager |
|-------------|-----------------|
| Cute | Cute |
| Exotic | Exotic |
| Beauty Mark | Beauty Mark |
| Cool Scars | Cool Scars |
| Small Scars / Horrific Scars | Scarred |
| Tattooed / Small Tattoos | Tattooed |
| Big Boobs / Busty Boobs / Giant Juggs | Large Breasts |
| Small Boobs / Petite Breasts | Small Breasts |
| Flat Chest | Flat Chest |
| Great Arse / Deluxe Derriere | Firm Ass |
| Plump Tush / Wide Bottom | Soft Ass |

### Species/Race Traits

| Whoremaster | Fantasy Manager |
|-------------|-----------------|
| (default) | Human |
| Elf | Elf |
| Dwarf | Dwarf |
| Demon | Demon |
| Angel | Angel |
| Not Human | Transformed |
| Cat Girl / Cow Girl / Furry | Transformed |
| Succubus | Demon |
| Vampire | Vampire |
| Dryad | Elf |

### Professional Traits

| Whoremaster | Fantasy Manager |
|-------------|-----------------|
| Adventurer | Adventurer |
| Maid | Maid |
| Singer | Singer |
| Teacher | Teacher |
| Waitress | Waitress |
| Chef | Waitress |
| Doctor | Teacher |
| Hunter | Adventurer |

### Sexual and Libido Traits

| Whoremaster | Fantasy Manager | Notes |
|-------------|-----------------|-------|
| Nymphomaniac | Nymph-Touched | Female, high libido, +Sex +Oral |
| (masculine hypersexual) | Beast Within | Male, high libido, +Sex +Group |
| High Sex Drive | Burning Desire | Libido regeneration +4/day |
| Insatiable | Insatiable | +6 regen, +15 max, +Sex +Group |
| Chaste | Frigid Soul | Cap libido to 5, cold work |
| (resistant) | Stamina of the Bull | +3 regen, +5 max, +5 health |
| (fragile) | Easily Spent | -3 regen, -5 max |
| (patient) | Slow Burn | -2 regen, +BDSM +Special |
| Fast Orgasms | Sensitive | +Sex +Oral +BDSM |
| Slow Orgasms | Numb | +BDSM +Extreme |
| Deep Throat | Pierced | +Oral +Sex |
| Charismatic | Charismatic | +Charm |
| Charming | Charming | +Charm |
| Elegant | Elegant | +Charm +Striptease |

---

## 📦 Item Mapping

### Item Types

| WM Type | FM Type |
|---------|---------|
| Ring, Necklace, Shoes, Boots, Hat, Glasses, Earring, Bracelet | accessory |
| Small Weapon, Large Weapon, Staff | weapon |
| Armor, Shield, Helmet | armor |
| Dress, Lingerie, Underwear, Outfit | clothing |
| Consumable, Food, Drug, Medicine, Makeup | consumable |
| Misc | accessory |

### Item Effects

| WM Effect | FM Effect |
|-----------|-----------|
| Skill: Combat | skill_modifiers.Combat |
| Stat: Charisma | skill_modifiers.Charm |
| Stat: Intelligence | skill_modifiers.Clever |
| Stat: Constitution | health |
| Stat: Tiredness | energy (inverted) |
| Stat: Libido | libido |
| Stat: Happiness | (no direct) |

---

## 📁 Image Folder Structure

### ✅ Good News: High Compatibility

**Fantasy Manager already understands most Whoremaster image names.**

FM's image search system is:
- **Case-insensitive** (case doesn't matter)
- **Searches multiple patterns** for each skill

### Names FM Already Understands (no renaming needed):

| WM Name | FM Skill | Notes |
|---------|----------|-------|
| `les`, `lesbian` | Homo | FM searches for "les" or "gay" |
| `gay` | Homo | ✅ Direct |
| `beast` | Extreme | FM searches for "beast" or "extreme" |
| `strip` | Striptease | FM searches for "strip" or "striptease" |
| `titty`, `tittysex` | Special | FM searches for "titty" or "special" |
| `wait`, `maid` | Service | FM searches for "wait", "service", "maid" |
| `sex`, `oral`, `anal`, `bdsm`, `group` | Direct | ✅ Same names |
| `combat`, `hand`, `charm` | Direct | ✅ Same names |

### Names that DO Need Renaming:

| WM Name | FM Name | Reason |
|---------|---------|--------|
| `Portrait` | `Profile` | FM searches for "profile", not "portrait" |
| `Foot`, `Footjob` | `hand` | FM doesn't search for "foot" |
| `Dildo`, `Mast` | `special` | Not in FM patterns |
| `Escort`, `Formal` | `charm` | Not in FM patterns |
| `Swim`, `Bath` | `rest` | For rest images |
| `Nurse`, `Shop` | `service` | Generic service |
| `Magic`, `Fight` | `craft`, `combat` | Simple rename |
| `Herd` | `extreme` | "beast" works, "herd" doesn't |

### Folder Structure

```
Whoremaster:                          Fantasy Manager:
Resources/Characters/                 game/images/workers/
├── Aeris Gainsborough/              └── aeris_gainsborough/
│   ├── Portrait.jpg    ───→            ├── Profile.jpg (rename)
│   ├── Sex.jpg         ───→            ├── Sex.jpg (works directly)
│   ├── Les.jpg         ───→            ├── Les.jpg (works directly!)
│   ├── Strip.jpg       ───→            ├── Strip.jpg (works directly!)
│   ├── Beast.gif       ───→            ├── Beast.webm (convert GIF)
│   └── ...                             └── ...
└── Aeris Gainsborough.girlsx        workers_wm.json (converted)
```

### Videos instead of GIFs

**Important**: Ren'Py cannot play animated GIFs. Use the converter to transform GIFs to WebM:

```bash
python rename_wm_images.py "character_folder" --convert-gifs
```

FM supports these video formats: `.webm`, `.mp4`, `.ogv`

---

## 🔧 Converter Usage

### Available Scripts

| Script | Description |
|--------|-------------|
| `wm_to_fm_converter.py` | Converts XML character/item data to JSON |
| `rename_wm_images.py` | Renames images and converts GIFs to WebM |

### 1. Data Converter (XML → JSON)

```bash
# Convert characters
python wm_to_fm_converter.py \
    --characters "C:/path/to/WM/Resources/Characters" \
    --output "workers_wm.json"

# Convert with image copy
python wm_to_fm_converter.py \
    --characters "C:/path/to/WM/Resources/Characters" \
    --output "workers_wm.json" \
    --copy-images \
    --image-dest "C:/path/to/FM/game/images/workers"

# Convert items
python wm_to_fm_converter.py \
    --items "C:/path/to/WM/Resources/Items" \
    --output "items_wm.json"
```

### 2. Image Converter

Most WM images work directly in FM. This script only:
- Renames images FM doesn't recognize (Portrait→Profile, etc.)
- Converts animated GIFs to WebM (Ren'Py doesn't support GIF)

```bash
# Preview what would be done (without changing anything)
python rename_wm_images.py "../game/images/workers/aeris" --dry-run

# Rename only
python rename_wm_images.py "../game/images/workers/aeris"

# Rename + Convert GIFs to WebM (requires ffmpeg)
python rename_wm_images.py "../game/images/workers/aeris" --convert-gifs

# Process ALL worker folders
python rename_wm_images.py "../game/images/workers" --all --convert-gifs
```

**Note**: For GIF conversion, you need [ffmpeg](https://ffmpeg.org/) installed and in PATH.

### Complete Practical Example

```bash
cd "C:\Users\Usuario\Desktop\SNS\FantasyManager\fantasy-manager\devkit"

# 1. Convert character data
python wm_to_fm_converter.py ^
    --characters "..\..\WM-7.2.2-win64 - copia\Resources\Characters" ^
    --output "..\game\data\workers\workers_wm.json" ^
    --copy-images ^
    --image-dest "..\game\images\workers"

# 2. Process images (rename + GIF→WebM)
python rename_wm_images.py "..\game\images\workers" --all --convert-gifs
```

---

## 💡 Improvement Proposals for Fantasy Manager

### 1. Expanded Libido System

**Current State**: FM has `libido` as a simple integer (0-20) that mainly affects success in sexual work.

**Improved Proposal**: Expand libido to create more gameplay dynamism:

```python
# In worker_defaults.rpy
worker.setdefault("libido", {
    "base": 10,          # Character base level (permanent)
    "current": 10,       # Current level (fluctuates)
    "max": 20,           # Maximum possible
    "regen_rate": 2,     # Regeneration per day without sexual work
    "decay_rate": 3,     # Reduction from intense sexual work
})
```

**Suggested mechanics**:
- **NSFW work reduces libido**: Each sexual job reduces `current` based on intensity
  - Sex, Oral: -1 to -2
  - Group, Extreme: -3 to -4
  - BDSM, Anal: -2 to -3
- **Low libido = Lower performance**: If `current < base * 0.5`, penalty to sexual skills
- **High libido = Bonus**: If `current > base * 1.5`, bonus to earnings and satisfaction
- **Regeneration**: +`regen_rate` per day of rest or non-sexual work
- **Traits affect libido** (already implemented):
  - "Burning Desire": +4 regen, +8 max
  - "Nymph-Touched" / "Beast Within": +5 regen, +12 max, min 10
  - "Insatiable": +6 regen, +15 max, min 8
  - "Frigid Soul": cap to 5
  - "Stamina of the Bull": +3 regen, +5 max
  - "Easily Spent": -3 regen, -5 max
  - "Slow Burn": -2 regen (but +BDSM)
- **Items**: Libido potions (aphrodisiacs) could temporarily increase

**Simplified implementation (alternative)**:
```python
# If you don't want complexity, simply:
worker.setdefault("libido_base", 10)  # Permanent
worker.setdefault("libido_current", 10)  # Fluctuates with work

# Regeneration in end_day
if worker["libido_current"] < worker["libido_base"]:
    worker["libido_current"] = min(
        worker["libido_base"], 
        worker["libido_current"] + 2
    )
```

### 2. Item Crafting System

WM has a crafting system. FM could add:

```python
item = {
    "id": "silver_ring",
    "crafting": {
        "required_skill": "Craft",
        "required_level": 20,
        "materials": ["silver_ore", "mana_crystal"],
        "craft_time": 2  # days
    }
}
```

### 3. GIF → WebM Conversion (Video)

Ren'Py **cannot play animated GIFs**, but **does support videos** (WebM, MP4).
The converter includes functionality to automatically convert GIFs to WebM:

```bash
# Convert image folder with GIFs
python rename_wm_images.py "../game/images/workers/aeris" --convert-gifs
```

Requires **ffmpeg** installed and in PATH.

### 4. Pregnancy/Fertility System (Future)

WM has a complete fertility/pregnancy system that could be added to FM in future versions.

---

## ⚠️ Conversion Limitations

1. **Traits without direct equivalent**: Some WM traits don't have an equivalent in FM and are lost or mapped to alternatives.

2. **Pregnancy System**: WM has a fertility/pregnancy system that FM doesn't implement yet.

3. **Disease System**: WM has STDs (AIDS, Herpes, etc.) that FM doesn't have.

4. **Animated GIFs**: Ren'Py doesn't support GIFs. Use converter to transform to WebM.

5. **Jobs vs Buildings**: WM uses a Jobs system, FM uses a Buildings system with different mechanics.

6. **WM Stats vs FM Traits**: 
   - WM has separate stats (Constitution, Beauty, Intelligence)
   - FM uses traits to represent these concepts (Strong, Beautiful, Clever)
   - Conversion doesn't create new stats, but assigns equivalent traits

---

## 📋 Conversion Checklist

### Step 1: Convert Data
- [ ] Run `wm_to_fm_converter.py` with `--copy-images`
- [ ] Verify generated JSON (workers_wm.json)
- [ ] Verify that image folders were copied

### Step 2: Process Images
- [ ] Run `rename_wm_images.py --dry-run` to preview
- [ ] Run `rename_wm_images.py --convert-gifs` to apply
- [ ] Verify that GIFs were converted to WebM

### Step 3: Verification
- [ ] Verify that each character has a Profile image
- [ ] Verify that traits were mapped correctly
- [ ] Manually adjust skills if necessary
- [ ] Test characters in the game

### Step 4: Items (Optional)
- [ ] Run converter on Items
- [ ] Merge converted items with existing items.json

---

## 🔄 Future Updates

This document will be updated as:
- New traits are added to Fantasy Manager
- New systems are implemented (pregnancy, diseases, etc.)
- The converter is improved with more options

**Last update**: December 2024
**Converter Version**: 1.0
