# Building Events Images Reference

## 📋 Image Types in Events

The building events system searches for 4 types of images:
1. **background_image** - Event background image
2. **success_image** - Success image (outcome: "success" or "critical_success")
3. **failure_image** - Failure image (outcome: "failure" or "mediocre")
4. **story_image** - Story image (for daily work in buildings)

## 🏛️ Background Images (Event Backgrounds)

### Building-Specific Events:
- **brothel_caution** - Caution event in brothel
- **brothel_health** - Health check event in brothel
- **restaurant_shortage** - Shortage event in restaurant
- **restaurant_banquet** - Banquet event in restaurant
- **guild_dragon** - Dragon event in guild
- **guild_raid** - Raid event in guild
- **tavern_brawl** - Brawl event in tavern
- **tavern_wine** - Wine crisis event in tavern
- **casino_rumors** - Rumors event in casino
- **casino_fraud** - Fraud event in casino

### Common Events:
- **duel_arena** - Knight duel
- **mystic_tent** - Mystic tent
- **guild_rivalry** - Guild rivalry
- **lost_heirloom** - Lost heirloom
- **kitchen_chaos** - Kitchen chaos
- **casino_table** - Casino table
- **brothel_private** - Private client in brothel
- **brothel_gift** - Secret gift in brothel
- **brothel_dance** - Dance in brothel
- **tavern_bard** - Bard in tavern
- **restaurant_panic** - Panic in restaurant

### Generic:
- **event_bg** - Generic background for events (used as fallback)

## ✅ Success Images (Success Images)

### Building-Specific:
- **brothel_success** - Success in brothel
- **restaurant_success** - Success in restaurant
- **guild_success** - Success in guild
- **tavern_success** - Success in tavern
- **casino_success** - Success in casino

### Event-Specific:
- **duel_success** - Success in duel
- **mystic_success** - Success with mystic
- **heirloom_success** - Success finding heirloom
- **kitchen_success** - Success in kitchen

### Generic:
- **generic_success** - Generic success (used as fallback)

## ❌ Failure Images (Failure Images)

### Building-Specific:
- **brothel_failure** - Failure in brothel
- **restaurant_failure** - Failure in restaurant
- **guild_failure** - Failure in guild
- **tavern_failure** - Failure in tavern
- **casino_failure** - Failure in casino

### Event-Specific:
- **duel_failure** - Failure in duel
- **mystic_failure** - Failure with mystic
- **heirloom_failure** - Failure finding heirloom
- **kitchen_failure** - Failure in kitchen

### Generic:
- **generic_failure** - Generic failure (used as fallback)

## 📖 Story Images (Daily Story Images)

These images are used for daily worker jobs in buildings:

### Brothel - Prostitute:
- **prostitute_vanilla** / **prostitute_vanilla_failure**
- **prostitute_anal** / **prostitute_anal_failure**
- **prostitute_bdsm** / **prostitute_bdsm_failure**
- **prostitute_oral** / **prostitute_oral_failure**
- **prostitute_hand** / **prostitute_hand_failure**
- **prostitute_homo** / **prostitute_homo_failure**
- **prostitute_group** / **prostitute_group_failure**
- **prostitute_vip** / **prostitute_vip_failure**

### Brothel - Stripper:
- **stripper_regular** / **stripper_regular_failure**
- **stripper_private** / **stripper_private_failure**
- **stripper_vip** / **stripper_vip_failure**

### Restaurant - Service:
- **service_story1** / **service_story1_failure**
- **service_story1_restaurant** / **service_story1_restaurant_failure**
- **Profile.jpg** (fallback, no failure)

### Restaurant - Cook:
- **cook_story1** / **cook_story1_failure**
- **cook_story2** / **cook_story2_failure**
- **Profile.jpg** (fallback, no failure)

### Adventurers Guild - Quest:
- **solo_quest** / **solo_quest_failure**
- **party_quest** / **party_quest_failure**
- **monster_capture** / **monster_capture_failure**
- **rest_adventurer** (no failure)

### Tavern - Bartender:
- **bartender_story1** / **bartender_story1_failure**

### Tavern - Entertainer:
- **entertainer_story1_tavern** / **entertainer_story1_tavern_failure**
- **entertainer_story2_tavern** / **entertainer_story2_tavern_failure**
- **Profile** (fallback, no failure)

### Casino - Guard:
- **guard_story1_casino** / **guard_story1_casino_failure**
- **guard_story2_casino** / **guard_story2_casino_failure**
- **rest_casino** (no failure)

## 🏷️ Applicable Prefixes and Suffixes

### Trait Prefixes (same as in skills):
The same trait prefixes apply to event images:
- **pregnant_** - If worker has "Pregnant" trait
- **futa_** - If worker has "Futa" trait
- **transformed_** - If worker has "Transformed" trait
- **magical_** - If worker has "Magical" trait
- **transformed_magical_**, **transformed_futa_**, **transformed_pregnant_**, **magical_futa_**, **magical_pregnant_**, **futa_pregnant_**, and all combinations of 3 and 4 traits (combinations)

### Outcome Suffixes:
- **_failure** - For failure results
- **(no suffix)** - For success results

## 📁 Search Structure

The system searches for images in this priority order:

### For Events (background_image, success_image, failure_image, story_image):
1. `{worker_folder}/{prefix}_{image_name}_{suffix}`
2. `{worker_folder}/{prefix}_{image_name}`
3. `{worker_folder}/{image_name}_{suffix}`
4. `{worker_folder}/{image_name}`
5. `images/workers/default/{prefix}_{image_name}_{suffix}`
6. `images/workers/default/{prefix}_{image_name}`
7. `images/workers/default/{image_name}_{suffix}`
8. `images/workers/default/{image_name}`

### For Backgrounds:
Backgrounds are searched directly with `renpy.loadable()`:
- `images/{background_image}.png` (or any valid extension)

## 📝 Filename Examples

### Background Images:
- `brothel_caution.png` - Caution event background
- `guild_dragon.png` - Dragon event background
- `tavern_brawl.png` - Tavern brawl background

### Success/Failure Images:
- `brothel_success.png` - Success in brothel
- `brothel_failure.png` - Failure in brothel
- `pregnant_brothel_success.png` - Success in brothel for pregnant workers
- `pregnant_brothel_failure.png` - Failure in brothel for pregnant workers

### Story Images:
- `prostitute_vanilla.png` - Prostitute vanilla story (success)
- `prostitute_vanilla_failure.png` - Prostitute vanilla story (failure)
- `pregnant_prostitute_anal.png` - Prostitute anal story for pregnant workers
- `cook_story1.png` - Cook story
- `cook_story1_failure.png` - Cook story (failure)

## 🎯 Supported File Formats

The system supports these formats:
- `.png`
- `.jpg`
- `.jpeg`
- `.webp`
- `.webm` (video)
- `.mp4` (video)

## 📊 Complete Summary

### Background Images (Total: 12 unique):
```
brothel_caution, brothel_health
restaurant_shortage, restaurant_banquet, restaurant_panic
guild_dragon, guild_raid, guild_rivalry
tavern_brawl, tavern_wine, tavern_bard
casino_rumors, casino_fraud, casino_table
duel_arena, mystic_tent, lost_heirloom, kitchen_chaos
brothel_private, brothel_gift, brothel_dance
event_bg (generic)
```

### Success Images (Total: 9 unique):
```
brothel_success, restaurant_success, guild_success
tavern_success, casino_success
duel_success, mystic_success, heirloom_success, kitchen_success
generic_success (generic)
```

### Failure Images (Total: 9 unique):
```
brothel_failure, restaurant_failure, guild_failure
tavern_failure, casino_failure
duel_failure, mystic_failure, heirloom_failure, kitchen_failure
generic_failure (generic)
```

### Story Images (Total: 20 unique):
```
prostitute_vanilla, prostitute_anal, prostitute_bdsm
prostitute_oral, prostitute_hand, prostitute_homo
prostitute_group, prostitute_vip
stripper_regular, stripper_private, stripper_vip
service_story1, service_story1_restaurant
cook_story1, cook_story2
solo_quest, party_quest, monster_capture, rest_adventurer
bartender_story1
entertainer_story1_tavern, entertainer_story2_tavern
guard_story1_casino, guard_story2_casino, rest_casino
Profile.jpg / Profile (fallback)
```

## 🔍 Important Notes

1. **Backgrounds vs Worker Images:**
   - `background_image` are searched in `images/` directly
   - `success_image`, `failure_image`, and `story_image` are searched in `images/workers/{folder}/` or `images/workers/default/`

2. **Automatic suffixes:**
   - If outcome is "failure" or "mediocre", searches for `{image}_failure`
   - If outcome is "success" or "critical_success", searches for `{image}` (without _failure)

3. **Trait prefixes:**
   - Applied the same as in skills: `pregnant_`, `futa_`, `transformed_`, and combinations

4. **Fallbacks:**
   - If specific image not found, uses `generic_success` or `generic_failure`
   - If story_image not found, uses `Profile.jpg` or `Profile`

5. **Flexible search:**
   - Case-insensitive
   - Searches pattern within filename
   - Supports numbered variations like `brothel_success (2).png`
