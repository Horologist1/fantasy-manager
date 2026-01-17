# Interactions System - Structure Guide

## System Overview

The interactions system has been reorganized to follow a clear and scalable structure:

### Base Structure
- **4 Categories**: Discipline, Romance, Friendship, Joy
- **4 Levels per category**:
  - **Level 1**: Always available
  - **Level 2**: Unlocked after 5 uses of Level 1
  - **Level 3**: Unlocked after 5 uses of Level 2
  - **Level 4**: Unlocked after 5 uses of Level 3 (farmable, optimal cost/benefit)

### Gender Combinations
Each interaction must have variants for:
- **Player**: Lord (male) or Lady (female)
- **Worker**: Male (masculine) or Female (feminine)

**Total**: 4 categories × 4 levels × 4 combinations = **64 base interactions**

## JSON Structure

Each interaction must have the following fields:

```json
{
  "id": "category_levelN_playerGender_workerGender",
  "name": "Interaction Name",
  "description": "Narrative description of what happens",
  "interaction_level": 1-4,
  "cost_energy": 1-4,
  "cost_money": 0-100,
  "effect": {
    "stat_name": value,
    "flags": {
      "cooldown_flag": {
        "value": true,
        "duration": days
      }
    }
  },
  "gender_filter": "male" | "female" | null,
  "worker_gender": "male" | "female" | null,
  "categories": ["CategoryName"],
  "image": "image_name",
  "nsfw": true | false,
  "stat_requirements": {},
  "required_flags": {},
  "excluded_flags": {}
}
```

## Cost and Effect Progression

### Level 1 (Basic)
- **Energy Cost**: 1
- **Money Cost**: 0-5
- **Effects**: Small (+2-5 in main stats)

### Level 2 (Intermediate)
- **Energy Cost**: 2
- **Money Cost**: 10-15
- **Effects**: Moderate (+5-12 in main stats)

### Level 3 (Advanced)
- **Energy Cost**: 3
- **Money Cost**: 25-35
- **Effects**: Large (+15-25 in main stats)
- **Note**: Can be NSFW

### Level 4 (Farmable)
- **Energy Cost**: 2 (optimized)
- **Money Cost**: 15-20 (optimized)
- **Effects**: Good (+15-20 in main stats)
- **Note**: Designed for repeated use with better cost/benefit

## Unlock System

The system automatically tracks uses of each level using flags:
- `{category}_uses_level_1`: Counter for level 1 uses
- `{category}_uses_level_2`: Counter for level 2 uses
- `{category}_uses_level_3`: Counter for level 3 uses

**Example**: To unlock Romance Level 2, 5 uses of Romance Level 1 are needed.

## Display System

When an interaction is executed:
1. The **description** is shown first (narrative text)
2. Then the **image** is shown as a "cutscene"
3. Effects and costs are applied

## Files

- `interactions_structured.json`: File with the new structure (complete example of Discipline)
- `interactions_main.json`: Original file (keep for compatibility or migrate)
- `interactions_special.json`: Special interactions for specific workers

## Implementation Notes

1. The filtering system automatically:
   - Filters by player gender (`gender_filter`)
   - Filters by worker gender (`worker_gender`)
   - Filters by unlock level (`interaction_level`)
   - Filters by required stats
   - Filters by required/excluded flags

2. Images must be in:
   - `images/workers/{worker_folder}/` (priority)
   - `images/workers/default/` (fallback)

3. The system is backward compatible: interactions without `interaction_level` are always shown.
