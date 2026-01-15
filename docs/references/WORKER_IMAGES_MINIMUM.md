# Minimum Image List for a Worker

## 🎯 Absolute Minimum Image (REQUIRED)

For a worker to function correctly in the game, they need **at least one profile image**:

### 1. Profile Image
- **Filename:** `Profile.png`, `Profile.jpg`, `Profile.jpeg`, `Profile.webp` (or numbered variations like `Profile (1).jpg`)
- **Location:** `game/images/workers/{worker_folder}/`
- **Description:** This is the image shown in the worker details screen, in the worker list, and as fallback when no other images are available.
- **Format:** Any supported format (png, jpg, jpeg, webp, webm, mp4)
- **Requirement:** ✅ **MANDATORY**

---

## 📸 Optional Images (Recommended)

Although not strictly necessary, these images improve the game experience:

### 2. Skill Images

The system searches for images based on worker skills. If a worker has a high skill, it's recommended to have images for it:

#### Standard Skills:
- `sex.png` / `sex.jpg` - For "Sex" skill
- `anal.png` / `anal.jpg` - For "Anal" skill
- `bdsm.png` / `bdsm.jpg` - For "BDSM" skill
- `hand.png` / `hand.jpg` - For "Hand" skill
- `oral.png` / `oral.jpg` - For "Oral" skill
- `les.png` or `gay.png` - For "Homo" skill
- `special.png` / `special.jpg` - For "Special" skill
- `group.png` / `group.jpg` - For "Group" skill
- `extreme.png` or `beast.png` - For "Extreme" skill
- `strip.png` or `striptease.png` - For "Striptease" skill
- `combat.png` / `combat.jpg` - For "Combat" skill
- `clever.png` / `clever.jpg` - For "Clever" skill
- `charm.png` / `charm.jpg` - For "Charm" skill
- `service.png` or `maid.png` - For "Service" skill
- `agility.png` / `agility.jpg` - For "Agility" skill
- `craft.png` / `craft.jpg` - For "Craft" skill

#### Result Variants:
- `{skill}_failure.png` - Image when skill fails (e.g., `sex_failure.png`)
- `{skill}.png` (no suffix) - Image when skill succeeds

**Note:** You can have multiple numbered variants: `sex (1).png`, `sex (2).png`, `sex (3).png`, etc.

### 3. Interaction Images (Optional)

If the worker participates in interactions, these images can be useful:

- `romance_female.png` - For romantic interactions (female workers)
- `romance_male.png` - For romantic interactions (male workers)
- `friendship.png` - For friendship interactions
- `joy_female.png` / `joy_male.png` - For joy interactions
- `obedience.png` - For discipline interactions

### 4. Event Images (Optional)

If the worker participates in specific events, you can create images for them:

- `{event_name}.png` - Event image (e.g., `cook_story1_restaurant.png`)
- `{event_name}_failure.png` - Event failure image

### 5. Images with Trait Prefixes (Optional)

If the worker has special traits, you can create specific images:

#### Individual Traits:
- `pregnant_{skill}.png` - If worker has "Pregnant" trait
- `futa_{skill}.png` - If worker has "Futa" trait
- `transformed_{skill}.png` - If worker has "Transformed" trait
- `magical_{skill}.png` - If worker has "Magical" trait

#### Combined Traits:
- `transformed_magical_futa_pregnant_{skill}.png` - If has all 4 traits
- `transformed_magical_futa_{skill}.png` - If has Transformed + Magical + Futa
- `transformed_magical_pregnant_{skill}.png` - If has Transformed + Magical + Pregnant
- `transformed_futa_pregnant_{skill}.png` - If has Transformed + Futa + Pregnant
- `magical_futa_pregnant_{skill}.png` - If has Magical + Futa + Pregnant
- `transformed_magical_{skill}.png` - If has Transformed + Magical
- `transformed_futa_{skill}.png` - If has Transformed + Futa
- `transformed_pregnant_{skill}.png` - If has Transformed + Pregnant
- `magical_futa_{skill}.png` - If has Magical + Futa
- `magical_pregnant_{skill}.png` - If has Magical + Pregnant
- `futa_pregnant_{skill}.png` - If has Futa + Pregnant

---

## 📋 Minimum Summary

### Minimum Folder Structure:
```
game/images/workers/{worker_folder}/
├── Profile.png (or Profile.jpg)  ← REQUIRED
```

### Recommended Folder Structure:
```
game/images/workers/{worker_folder}/
├── Profile.png (or Profile.jpg)  ← REQUIRED
├── sex.png                      ← Optional (if has Sex skill)
├── sex_failure.png              ← Optional (failure variant)
├── anal.png                     ← Optional (if has Anal skill)
├── oral.png                     ← Optional (if has Oral skill)
└── ... (more images according to skills)
```

---

## 🎨 Supported Formats

The system supports these image/video formats:
- `.png` ✅
- `.jpg` ✅
- `.jpeg` ✅
- `.webp` ✅
- `.webm` (video) ✅
- `.mp4` (video) ✅

---

## 📝 Important Notes

1. **Flexible Search:** The system searches for images flexibly:
   - Case-insensitive
   - Searches pattern within filename
   - Supports numbered variations: `sex (1).png`, `sex (2).png`, etc.

2. **Fallback:** If a specific image is not found, the system uses the profile image as fallback.

3. **Cache:** The system uses cache to maintain visual consistency during the same Daily Report.

4. **Search Priority:**
   - First searches in worker folder
   - Then searches in default folder (`images/workers/aspen/`)
   - Finally uses profile image

---

## ✅ Minimum Checklist for a Worker

- [ ] **Profile image** (`Profile.png` or `Profile.jpg`) in `game/images/workers/{folder}/`
- [ ] The `"folder"` field in the worker JSON matches the folder name
- [ ] The image is in a supported format (png, jpg, jpeg, webp)

**With just these 3 requirements, the worker will function correctly in the game.**
