# WM → FM Import Documentation

## 📋 What does the WM Import do?

The Fantasy Manager Editor v4 includes integrated Whoremaster import functionality. It transforms Whoremaster XML files (`.girlsx`, `.rgirlsx`) to Fantasy Manager's JSON format.

**Note:** The standalone converter has been deprecated. All import functionality is now in the Editor v4.

---

## 🎯 Character Conversion Process

### 1. **XML Reading**
- Reads `.girlsx` files (unique characters) and `.rgirlsx` files (random templates)
- Extracts: name, description, stats, skills, traits

### 2. **Skill Mapping**
The editor maps WM skills to FM using `WM_SKILL_MAPPING`:

```python
"NormalSex" → "Sex"
"OralSex" → "Oral"
"Lesbian" → "Homo"
"Handjob" → "Hand"
"TittySex" → "Special"
"Beastiality" → "Extreme"
"Strip" → "Striptease"
"Magic" → "Craft"
"Medicine" → "Clever"
"Performance" → "Charm"
# etc...
```

**Default values:** All skills start at 5, then WM values are added.

### 3. **Stats → Skills Mapping**
WM stats contribute to FM skills:

```python
"Charisma" → "Charm" (factor 0.5)
"Intelligence" → "Clever" (factor 0.5)
"Agility" → "Agility" (factor 1.0)
"Strength" → "Combat" (factor 0.3)
"Beauty" → "Charm" (factor 0.2)
"Libido" → "Sex" (factor 0.2)
# etc...
```

### 4. **Trait Mapping** ⚠️ **IMPORTANT**

The editor uses `WM_TRAIT_MAPPING` to convert traits. **Rules:**

- ✅ **Mapped traits:** Converted to FM equivalent
- ❌ **Unmapped traits:** Logged but NOT added to character
- Only traits that exist in FM's `traits.json` are added

**Examples:**
```python
"Nymphomaniac" → "Nymph-Touched"
"Chaste" → "Frigid Soul"
"High Sex Drive" → "Burning Desire"
"Slut" → "Insatiable"
"Big Boobs" → "Large Breasts"
# etc...
```

### 5. **File Type Rules**

| Extension | Type | unique | encounter_only | procedural |
|-----------|------|--------|----------------|------------|
| `.girlsx` | Unique worker | true | true | false |
| `.rgirlsx` | Random template | false | false | true |

---

## 🖼️ Image Handling

### Image Folder Copy
- The editor copies the entire image folder from WM to FM
- Folder is renamed to match FM conventions (lowercase, underscores)

### Image Renaming (WM → FM)

The editor automatically renames images for FM compatibility:

#### Pregnant Images
WM uses "Preg" prefix, FM uses "pregnant_":

| WM Original | FM Converted |
|-------------|--------------|
| `Preg.jpg` | `pregnant_profile.jpg` |
| `Preg (2).jpg` | `pregnant_profile (2).jpg` |
| `PregSex.jpg` | `pregnant_sex.jpg` |
| `PregGroup.jpeg` | `pregnant_group.jpeg` |
| `PregNude.jpeg` | `pregnant_strip.jpeg` |
| `PregBeast.jpg` | `pregnant_extreme.jpg` |
| `Preggo.jpg` | `pregnant_profile.jpg` |
| `PreggoSex.png` | `pregnant_sex.png` |

#### Other Renames

| WM Original | FM Converted | Reason |
|-------------|--------------|--------|
| `Portrait.jpg` | `profile.jpg` | FM uses "profile" |
| `Foot.jpg` | `hand.jpg` | FM doesn't search "foot" |
| `Dildo.jpg` | `special.jpg` | Maps to Special skill |
| `Escort.jpg` | `charm.jpg` | Maps to Charm skill |
| `Swim.jpg` | `rest.jpg` | Maps to rest |
| `Nude.jpg` | `strip.jpg` | Maps to Striptease |
| `Dom.jpg` | `bdsm.jpg` | Maps to BDSM skill |
| `Magic.jpg` | `craft.jpg` | Maps to Craft skill |
| `Jail.jpg` | `combat_failure.jpg` | Failure image |

### GIF to WebM Conversion
- Ren'Py doesn't support GIF animations
- The editor converts GIFs to WebM videos using FFmpeg
- Requires FFmpeg to be installed (the editor will offer to install it)

---

## 🔧 Usage (Editor v4)

1. Open Fantasy Manager Editor v4
2. Go to the "🔄 WM Import" tab
3. Select your Whoremaster Characters folder
4. Click "Scan" to find all character files
5. Select characters to import (or click "Import All")
6. Options:
   - ✅ Copy image folders
   - ✅ Rename images for FM compatibility
   - ✅ Convert GIFs to WebM
7. Click "Import Selected" or "Import All"
8. Workers are saved to the specified JSON file

---

## 📁 FFmpeg Installation

FFmpeg is required for GIF to WebM conversion.

### Windows (Recommended)
Using winget:
```
winget install FFmpeg
```

Or using Chocolatey:
```
choco install ffmpeg
```

### Manual Installation
1. Download from: https://ffmpeg.org/download.html
2. Extract to a folder (e.g., `C:\ffmpeg`)
3. Add the `bin` folder to your PATH environment variable
4. Restart the editor

The editor will check for FFmpeg and show instructions if not found.
