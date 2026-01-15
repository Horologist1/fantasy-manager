# Available Interactions List

This document lists all interactions in the system organized by category, level, and gender combinations.

---

## 📋 General Structure

Each category has **4 levels**:
- **Level 1**: Always available
- **Level 2**: Unlocked after 5 uses of Level 1
- **Level 3**: Unlocked after 5 uses of Level 2
- **Level 4**: Unlocked after 5 uses of Level 3 (farmable, optimal cost/benefit)

Each level has variants for **4 gender combinations**:
- Lord (male) + Female Worker
- Lord (male) + Male Worker
- Lady (female) + Female Worker
- Lady (female) + Male Worker

---

## ⚔️ DISCIPLINE

### Level 1 - Basic
**Cost:** 1 Energy | 0 Money

| ID | Name | Player | Worker | Effects |
|---|---|---|---|---|
| `discipline_level1_lord_female` | Gentle Correction | Lord | Female | -3 rebelliousness, +1 relationship |
| `discipline_level1_lord_male` | Direct Talk | Lord | Male | -3 rebelliousness, +1 relationship |
| `discipline_level1_lady_female` | Kind Guidance | Lady | Female | -3 rebelliousness, +1 relationship |
| `discipline_level1_lady_male` | Respectful Reminder | Lady | Male | -3 rebelliousness, +1 relationship |

### Level 2 - Intermediate
**Cost:** 2 Energy | 10 Money

| ID | Name | Player | Worker | Effects |
|---|---|---|---|---|
| `discipline_level2_lord_female` | Firm Training | Lord | Female | -5 rebelliousness, +2 relationship |
| `discipline_level2_lord_male` | Intensive Training | Lord | Male | -5 rebelliousness, +2 relationship |
| `discipline_level2_lady_female` | Structured Guidance | Lady | Female | -5 rebelliousness, +2 relationship |
| `discipline_level2_lady_male` | Rigorous Instruction | Lady | Male | -5 rebelliousness, +2 relationship |

### Level 3 - Advanced
**Cost:** 3 Energy | 0 Money | ⚠️ NSFW

| ID | Name | Player | Worker | Effects |
|---|---|---|---|---|
| `discipline_level3_lord_female` | Complete Submission | Lord | Female | -7 rebelliousness, +3 relationship, +2 romance |
| `discipline_level3_lord_male` | Alpha Dominance | Lord | Male | -7 rebelliousness, +3 relationship, +2 romance |
| `discipline_level3_lady_female` | Absolute Obedience | Lady | Female | -7 rebelliousness, +3 relationship, +2 romance |
| `discipline_level3_lady_male` | Total Submission | Lady | Male | -7 rebelliousness, +3 relationship, +2 romance |

**Requirements:** relationship ≥ 20

### Level 4 - Farmable
**Cost:** 2 Energy | 0 Money

| ID | Name | Player | Worker | Effects |
|---|---|---|---|---|
| `discipline_level4_lord_female` | Perfect Discipline | Lord | Female | -6 rebelliousness, +3 relationship |
| `discipline_level4_lord_male` | Masterful Control | Lord | Male | -6 rebelliousness, +3 relationship |
| `discipline_level4_lady_female` | Elegant Authority | Lady | Female | -6 rebelliousness, +3 relationship |
| `discipline_level4_lady_male` | Refined Command | Lady | Male | -6 rebelliousness, +3 relationship |

**Requirements:** relationship ≥ 30

---

## 💕 ROMANCE

### Level 1 - Basic
**Cost:** 1 Energy | 0 Money

| ID | Name | Player | Worker | Effects |
|---|---|---|---|---|
| `romance_level1_lord_female` | Charming Banter | Lord | Female | +3 romance, +1 relationship |
| `romance_level1_lord_male` | Charming Banter | Lord | Male | +3 romance, +1 relationship |
| `romance_level1_lady_female` | Playful Flirting | Lady | Female | +3 romance, +1 relationship |
| `romance_level1_lady_male` | Elegant Flirtation | Lady | Male | +3 romance, +1 relationship |

**Requirements:** relationship ≥ 10 (Lord+Male/Female), relationship ≥ 15 (Lady+Female)

### Level 2 - Intermediate
**Cost:** 2 Energy | 20 Money

| ID | Name | Player | Worker | Effects |
|---|---|---|---|---|
| `romance_level2_lord_female` | Private Connection | Lord | Female | +5 romance, +2 relationship |
| `romance_level2_lord_male` | Intimate Evening | Lord | Male | +5 romance, +2 relationship |
| `romance_level2_lady_female` | Intimate Evening | Lady | Female | +5 romance, +2 relationship |
| `romance_level2_lady_male` | Private Adventure | Lady | Male | +5 romance, +2 relationship |

**Requirements:** romance ≥ 10, relationship ≥ 15 (Lord), relationship ≥ 20 (Lady+Female)

### Level 3 - Advanced
**Cost:** 3 Energy | 12 Money | ⚠️ NSFW

| ID | Name | Player | Worker | Effects |
|---|---|---|---|---|
| `romance_level3_lord_female` | Dominant Union | Lord | Female | +7 romance, +3 relationship, +2 joy |
| `romance_level3_lord_male` | Passionate Night | Lord | Male | +7 romance, +3 relationship, +2 joy |
| `romance_level3_lady_female` | Passionate Night | Lady | Female | +7 romance, +3 relationship, +2 joy |
| `romance_level3_lady_male` | Epic Adventure | Lady | Male | +7 romance, +3 relationship, +2 joy |

**Requirements:** romance ≥ 20, relationship ≥ 25 (Lord), relationship ≥ 30 (Lady+Female)

### Level 4 - Farmable
**Cost:** 2 Energy | 10 Money

| ID | Name | Player | Worker | Effects |
|---|---|---|---|---|
| `romance_level4_lord_female` | Perfect Romance | Lord | Female | +6 romance, +3 relationship, +2 joy |
| `romance_level4_lord_male` | Masterful Romance | Lord | Male | +6 romance, +3 relationship, +2 joy |
| `romance_level4_lady_female` | Elegant Romance | Lady | Female | +6 romance, +3 relationship, +2 joy |
| `romance_level4_lady_male` | Refined Romance | Lady | Male | +6 romance, +3 relationship, +2 joy |

**Requirements:** romance ≥ 30, relationship ≥ 30

---

## 🤝 FRIENDSHIP

*Note: Friendship interactions are not yet implemented in `interactions_structured.json`. They can be added following the same pattern.*

### Proposed Structure:

**Level 1:** Friendly Chat / Casual Conversation
- Cost: 1 Energy | 0 Money
- Effects: +3 relationship

**Level 2:** Heart-to-Heart / Brotherhood Bond
- Cost: 2 Energy | 5-8 Money
- Effects: +5 relationship, +2 joy

**Level 3:** Soul Sisters / Blood Brothers
- Cost: 3 Energy | 15-20 Money
- Effects: +7 relationship, +3 joy, +2 romance

**Level 4:** Perfect Friendship (Farmable)
- Cost: 2 Energy | 5-8 Money
- Effects: +6 relationship, +3 joy

---

## 🎉 JOY

*Note: Joy interactions are not yet implemented in `interactions_structured.json`. They can be added following the same pattern.*

### Proposed Structure:

**Level 1:** Thoughtful Gift / Practical Present
- Cost: 1 Energy | 8-10 Money
- Effects: +3 joy, +1 relationship

**Level 2:** Luxury Experience / Adventure Trip
- Cost: 2 Energy | 25-30 Money
- Effects: +5 joy, +2 relationship, +1 romance

**Level 3:** Ultimate Fantasy / Epic Achievement
- Cost: 3 Energy | 50-60 Money
- Effects: +7 joy, +3 relationship, +2 romance

**Level 4:** Perfect Joy (Farmable)
- Cost: 2 Energy | 15-20 Money
- Effects: +6 joy, +3 relationship, +2 romance

---

## 🎭 SPECIFIC INTERACTIONS

These interactions are designed for specific workers or with special traits.

### Violet's Special Performance
- **ID:** `violet_special`
- **Category:** Romance
- **Specific Worker:** Violet
- **Cost:** 3 Energy | 0 Money
- **Effects:** +30 romance, +15 relationship, +20 joy
- **Requirements:** romance ≥ 0
- **Cooldown:** 5 days

### Enchanting Presence
- **ID:** `charming_beauty`
- **Category:** Romance
- **Required Traits:** Beautiful, Charming
- **Cost:** 3 Energy | 0 Money
- **Effects:** +35 romance, +20 joy, +15 relationship
- **Requirements:** romance ≥ 15
- **Cooldown:** 4 days

---

## 📊 Cost Summary by Category

### Discipline
| Level | Energy | Money | Type |
|-------|---------|--------|------|
| 1 | 1 | 0 | Basic |
| 2 | 2 | 10 | Intermediate |
| 3 | 3 | 0 | Advanced (NSFW) |
| 4 | 2 | 0 | Farmable |

### Romance
| Level | Energy | Money | Type |
|-------|---------|--------|------|
| 1 | 1 | 0 | Basic |
| 2 | 2 | 20 | Intermediate |
| 3 | 3 | 12 | Advanced (NSFW) |
| 4 | 2 | 10 | Farmable |

### Friendship (Proposed)
| Level | Energy | Money | Type |
|-------|---------|--------|------|
| 1 | 1 | 0 | Basic |
| 2 | 2 | 5-8 | Intermediate |
| 3 | 3 | 15-20 | Advanced |
| 4 | 2 | 5-8 | Farmable |

### Joy (Proposed)
| Level | Energy | Money | Type |
|-------|---------|--------|------|
| 1 | 1 | 8-10 | Basic |
| 2 | 2 | 25-30 | Intermediate |
| 3 | 3 | 50-60 | Advanced |
| 4 | 2 | 15-20 | Farmable |

---

## 🔓 Unlock System

The system automatically tracks uses of each level using flags:
- `{category}_uses_level_1`: Counter for level 1 uses
- `{category}_uses_level_2`: Counter for level 2 uses
- `{category}_uses_level_3`: Counter for level 3 uses

**Example:** To unlock Romance Level 2, 5 uses of Romance Level 1 are needed.

---

## 📝 Notes

- All interactions have cooldowns to prevent spam
- NSFW interactions require `persistent.nsfw_enabled` to be active
- Specific interactions appear only for the indicated workers
- Trait interactions appear only for workers with those traits
- The system is backward compatible: interactions without `interaction_level` are always shown

---

*Last update: Interactions system reorganized with 4-level structure per category*
