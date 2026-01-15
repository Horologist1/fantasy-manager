# Skills System Images Reference

## 📋 Skills the System Searches For

The system searches for images using these skill names (lowercase):

### Standard Skills:
1. **sex** - Searches directly for "sex"
2. **anal** - Searches directly for "anal"
3. **bdsm** - Searches directly for "bdsm"
4. **hand** - Searches directly for "hand"
5. **oral** - Searches directly for "oral"
6. **homo** - Searches for **"les"** OR **"gay"** (multiple patterns)
7. **special** - Searches directly for "special"
8. **group** - Searches directly for "group"
9. **extreme** - Searches for **"extreme"** OR **"beast"** (multiple patterns)
10. **striptease** - Searches for **"strip"** OR **"striptease"** (multiple patterns)
11. **combat** - Searches directly for "combat"
12. **clever** - Searches directly for "clever"
13. **charm** - Searches directly for "charm"
14. **wait** - Searches for **"service"** OR **"maid"** (multiple patterns)
15. **agility** - Searches directly for "agility"
16. **craft** - Searches directly for "craft"
17. **Specialty 4-12** - Searches directly for the name (lowercase)

## 🏷️ Trait Prefixes

The system searches for images with these prefixes based on worker traits:

### Individual Prefixes:
- **pregnant_** - If worker has "Pregnant" trait
- **futa_** - If worker has "Futa" trait
- **transformed_** - If worker has "Transformed" trait
- **magical_** - If worker has "Magical" trait

### Combined Prefixes (in priority order):
1. **transformed_magical_futa_pregnant_** - If has all 4 traits
2. **transformed_magical_futa_** - If has Transformed + Magical + Futa
3. **transformed_magical_pregnant_** - If has Transformed + Magical + Pregnant
4. **transformed_futa_pregnant_** - If has Transformed + Futa + Pregnant
5. **magical_futa_pregnant_** - If has Magical + Futa + Pregnant
6. **transformed_magical_** - If has Transformed + Magical
7. **transformed_futa_** - If has Transformed + Futa
8. **transformed_pregnant_** - If has Transformed + Pregnant
9. **magical_futa_** - If has Magical + Futa
10. **magical_pregnant_** - If has Magical + Pregnant
11. **futa_pregnant_** - If has Futa + Pregnant

**Note:** Priority order is: Transformed > Magical > Futa > Pregnant

## 🔖 Outcome Suffixes

### Result Suffixes:
- **_failure** - For failure results (outcome: "failure" or "mediocre")
- **(no suffix)** - For success results (outcome: "success" or "critical_success")

## 📁 Image Search Structure

The system searches for images in this priority order:

### For Skills:
1. `{worker_folder}/{prefix}_{skill}_{suffix}`
2. `{worker_folder}/{prefix}_{skill}`
3. `{worker_folder}/{skill}_{suffix}`
4. `{worker_folder}/{skill}`
5. `images/workers/default/{prefix}_{skill}_{suffix}`
6. `images/workers/default/{prefix}_{skill}`
7. `images/workers/default/{skill}_{suffix}`
8. `images/workers/default/{skill}`

### For Events (story_image):
1. `{worker_folder}/{prefix}_{story_image}_{suffix}`
2. `{worker_folder}/{prefix}_{story_image}`
3. `{worker_folder}/{story_image}_{suffix}`
4. `{worker_folder}/{story_image}`
5. `images/workers/default/{prefix}_{story_image}_{suffix}`
6. `images/workers/default/{prefix}_{story_image}`
7. `images/workers/default/{story_image}_{suffix}`
8. `images/workers/default/{story_image}`

## 📝 Filename Examples

### Examples with Skills:
- `sex.png` - General sex image
- `sex_failure.png` - Failure image for sex
- `pregnant_sex.png` - Sex image for pregnant workers
- `pregnant_sex_failure.png` - Failure sex image for pregnant workers
- `futa_anal.png` - Anal image for futa workers
- `transformed_futa_oral.png` - Oral image for transformed + futa workers
- `les.png` or `gay.png` - Images for "homo" skill
- `service.png` or `maid.png` - Images for "wait" skill
- `strip.png` or `striptease.png` - Images for "striptease" skill
- `extreme.png` or `beast.png` - Images for "extreme" skill

### Examples with Events:
- `brothel_success.png` - Success image for brothel event
- `brothel_failure.png` - Failure image for brothel event
- `pregnant_brothel.png` - Brothel image for pregnant workers
- `pregnant_brothel_failure.png` - Failure brothel image for pregnant workers

## 🎯 Supported File Formats

The system supports these image/video formats:
- `.png`
- `.jpg`
- `.jpeg`
- `.webp`
- `.webm` (video)
- `.mp4` (video)

## 🔍 Flexible Search

The system uses flexible search that:
- Is **case-insensitive** (doesn't distinguish uppercase/lowercase)
- Searches for pattern **within filename** (doesn't require exact match)
- Supports numbered variations like `sex (2).png`, `sex (3).png`, etc.

## 📌 Important Notes

1. **Prefix exclusion:** If a worker does NOT have a trait, the system automatically excludes files starting with that prefix (e.g., if not pregnant, doesn't search for `pregnant_*.png`)

2. **Profile images:** The system also searches for profile images with pattern `profile.*` as fallback

3. **Cache:** The system uses cache to maintain visual consistency during the same Daily Report

4. **Special skills:** Some skills search for multiple patterns:
   - `homo` → searches for "les" AND "gay"
   - `wait` → searches for "service" AND "maid"
   - `striptease` → searches for "strip" AND "striptease"
   - `extreme` → searches for "extreme" AND "beast"

## 📊 Search Pattern Summary

### Base Patterns by Skill:
```
sex, anal, bdsm, hand, oral, special, group, extreme, combat, clever, charm, agility, craft
les, gay (for homo)
service, maid (for wait)
strip, striptease (for striptease)
extreme, beast (for extreme)
```

### Patterns with Prefixes:
```
pregnant_{skill}
futa_{skill}
transformed_{skill}
magical_{skill}
transformed_magical_{skill}
transformed_futa_{skill}
transformed_pregnant_{skill}
magical_futa_{skill}
magical_pregnant_{skill}
futa_pregnant_{skill}
transformed_magical_futa_{skill}
transformed_magical_pregnant_{skill}
transformed_futa_pregnant_{skill}
magical_futa_pregnant_{skill}
transformed_magical_futa_pregnant_{skill}
```

### Patterns with Suffixes:
```
{skill}_failure
{prefix}_{skill}_failure
```

### Complete Patterns:
```
{prefix}_{skill}
{prefix}_{skill}_failure
{skill}
{skill}_failure
```
