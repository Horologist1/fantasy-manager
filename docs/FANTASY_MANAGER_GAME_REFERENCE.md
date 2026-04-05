# Fantasy Manager - Complete Game Reference

## 📖 Overview

**Fantasy Manager** is a worker management simulator set in a fantasy world. The player manages a business (tavern, brothel, etc.) by assigning workers to different professions, improving their skills, and generating income through daily events.

### Core Concept
- Manage workers by assigning them to buildings and professions
- Workers perform daily events that generate money and reputation
- Improve skills, levels, and relationships with workers
- Manage resources: money, reputation, item inventory
- Calendar system with days, months, and years

---

## 🎮 Core Mechanics

### 1. Calendar System

**Structure:**
- 7 days per week: Monareth, Tuelivane, Wetheris, Thurramor, Freylorn, Starrith, Sundusk
- 12 months per year: Frostveil, Glimmerthaw, Eldergreen, Blossomire, Solstara, Mistralune, Harvestide, Duskmoor, Shadowfen, Crystalfell, Emberwane, Nightspire
- 28 days per month
- Time advances automatically each day

**Functions:**
- `advance_date()` - Advances one day, updates month/year if needed
- `calculate_total_days()` - Calculates total days since start (year 1, month 1, day 1)
- `sync_calendar()` - Synchronizes calendar between store and persistent

---

### 2. Workers System

#### Data Structure

```python
worker = {
    "name": str,                    # Unique name
    "folder": str,                  # Image folder (e.g., "aspen")
    "gender": str,                  # "male" or "female"
    "level": int,                   # Level (1+)
    "skills": dict,                 # {"Sex": 50, "Charm": 30, ...}
    "original_skills": dict,        # Base skills (without modifiers)
    "traits": list,                 # ["Human", "Beautiful", "Charming", ...]
    "inventory": list,              # [(item_id, quantity, equipped), ...]
    "health": int,                  # Current health
    "energy": int,                  # Current energy
    "joy": int,                     # Happiness (0-100)
    "rebelliousness": int,          # Rebelliousness (0-100)
    "romance": int,                 # Romance (0-100)
    "relationship": int,           # Relationship with player (0-100)
    "libido": int,                  # Libido (0-20+)
    "comfort_level": int,          # Current comfort level (1-5)
    "comfort_desired": int,         # Desired comfort (1-5)
    "success_count": int,           # Success counter for leveling up
    "failed_rolls": int,            # Failure counter
    "skill_uses": dict,             # {"Sex": 2, "Charm": 1, ...} - daily usage
    "cost": int,                    # Purchase cost
    "unique": bool,                 # Whether unique or not
    "encounter_only": bool,         # Only available in encounters
    "procedural": bool,             # Procedurally generated
    "monster": bool,                # Whether monster
    "nsfw": bool,                   # Whether NSFW
    "description": str,             # Description
    "names_list": str,              # Name pool (e.g., "western_female")
}
```

#### Main Attributes

**Skills:**
- **NSFW:** Sex, Anal, BDSM, Hand, Oral, Homo, Special, Group, Extreme, Striptease
- **SFW:** Combat, Clever, Charm, Service, Agility, Craft
- **Special:** Specialty 4-12 (reserved for expansions)
- **Range:** 0-100 (base), but can exceed 100 with modifiers

**Secondary Attributes:**
- **Health:** 10 + (level × 5) + trait modifiers
- **Energy:** level × 5 + trait modifiers
- **Joy:** 0-100 (worker happiness)
- **Rebelliousness:** 0-100 (rebelliousness, affects if they accept work)
- **Romance:** 0-100 (romance with player)
- **Relationship:** 0-100 (relationship with player)
- **Libido:** 0-20+ (sexual desire, affects sexual skills)
- **Comfort Level:** 1-5 (current comfort level)
- **Comfort Desired:** 1-5 (comfort the worker desires)

#### Skill Calculations

**Effective Skill Formula:**
```python
effective_skill = base_skill + trait_bonus + equipment_bonus + libido_bonus
```

- **Base Skill:** `worker["skills"][skill_name]` (capped at 100)
- **Trait Bonus:** Sum of `skill_modifiers` from all traits
- **Equipment Bonus:** Sum of `skill_modifiers` from equipped items
- **Libido Bonus:** Only for sexual skills = `libido / 2` (only in NSFW mode)

**Example:**
- Base Sex: 50
- Trait "Nympho": +3 Sex
- Equipped item: +2 Sex
- Libido: 10 → Bonus: +5
- **Total:** 50 + 3 + 2 + 5 = 60

#### Health/Energy Calculations

**Max Health:**
```python
max_health = 10 + (level × 5) + sum(trait.health for traits)
```

**Max Energy:**
```python
max_energy = (level × 5) + sum(trait.energy for traits)
```

**Health Regeneration:**
```python
health_regen = level + calculate_health_regeneration(worker)
# Where calculate_health_regeneration returns: 1 + sum(trait.health_regeneration for traits)
```

#### Leveling System

**Level Up:**
- Requirement: `success_count >= 20 × current_level`
- On level up:
  - `level += 1`
  - `success_count = 0`
  - `rebelliousness -= comfort_level` (reduction from progress)

**Skill Up:**
- Requirement: `success_count >= 10 × current_skill`
- On skill up:
  - `skill += 1` (capped at 100)
  - `success_count = 0`
  - `rebelliousness -= comfort_level` (reduction from progress)

---

### 3. Traits System

#### Trait Structure

```json
{
    "name": "Beautiful",
    "conflicts": [],                    // Incompatible traits
    "removes_traits": [],               // Traits it removes
    "modifiers": {
        "earnings_multiplier": 1.2,     // Earnings multiplier
        "skill_modifiers": {             // Skill bonuses
            "Charm": 2
        },
        "health": 5,                     // Health bonus
        "energy": 10,                    // Energy bonus
        "health_regeneration": 1,        // Regeneration bonus
        "libido": 5,                     // Libido bonus
        "libido_regeneration": 3,       // Libido regeneration bonus
        "libido_max": 10,                // Max libido bonus
        "rebelliousness": -10,          // Rebelliousness modifier
        "joy": 20,                       // Joy modifier
        "relationship": 10              // Relationship modifier
    },
    "description": "...",
    "nsfw": false,                       // Whether NSFW
    "gender_restriction": "female",     // Gender restriction (optional)
    "requires_traits": ["Magical"],     // Required traits (optional)
    "attribute_caps": {                  // Attribute limits
        "rebelliousness": 40
    },
    "attribute_minimums": {              // Attribute minimums
        "libido": 10
    },
    "duration": 7,                      // Duration in days (optional, for temporary traits)
    "only_assigned": true               // Only when assigned (optional)
}
```

#### Trait Types

1. **Racial:** Human, Elf, Dwarf, Orc, Demon, Angel, Vampire, Goblin, Transformed
2. **Physical:** Large Breasts, Small Breasts, Flat Chest, Firm Ass, Soft Ass, Tall, etc.
3. **Personality:** Charming, Confident, Nervous, Optimist, Pessimist, etc.
4. **Professional:** Maid, Singer, Teacher, Waitress, Actress, Porn Star, etc.
5. **Magical:** Magical, Strong Magic, Powerful Magic, Psychic (require Magical)
6. **Sexual/NSFW:** Futa, Nympho, Satyr, Masochist, Pierced Tongue, etc.
7. **Temporary:** Pregnant, Sick, Cursed Vitality, etc.

#### Conflicts and Removals

- **Conflicts:** If a worker has a conflicting trait, they cannot have the other
- **Removes_traits:** When adding this trait, listed traits are automatically removed
- **Example:** "Rebellious" conflicts with "Dependant" and "Obedient"

---

### 4. Earnings System

#### Base Formula

```python
# 1. Base earnings from event
base_earnings = eval(earnings_formula, {"skill": effective_skill, "level": level})

# 2. Outcome adjustment
if outcome == "Critical Success":
    earnings = base_earnings × 0.65
elif outcome == "Success":
    earnings = base_earnings × 0.75
elif outcome == "Mediocre":
    earnings = base_earnings × 0.75
else:  # Failure
    earnings = base_earnings × 2 (if negative) or -10 (if 0)

# 3. Relevant trait bonus (50% chance if success/critical)
if random() < 0.5 and outcome in ["Success", "Critical Success"]:
    for trait in worker.traits:
        if trait in story.relevant_traits:
            bonus += eval(trait_bonus_formula, {"level": level}) × 0.3  # Reduced to 30%

# 4. Apply trait multipliers
earnings = calculate_earnings(worker, earnings)
```

#### Trait Multiplier Calculation

```python
multiplier = 1.0
for trait in worker.traits:
    per_trait = trait.earnings_multiplier
    per_trait = min(per_trait, 1.15)  # Cap per trait: 1.15x
    multiplier *= per_trait
    if trait in client_seeked_traits:
        multiplier *= 1.2  # Bonus if client seeks that trait

multiplier = min(multiplier, 1.6)  # Total cap: 1.6x
final_earnings = base_earnings × multiplier
```

**Example:**
- Base earnings: $100
- Traits: Beautiful (1.2x), Charming (1.15x), Exotic (1.25x)
- Multiplier: 1.2 × 1.15 × 1.25 = 1.725 → capped to 1.6
- **Final:** $100 × 1.6 = $160

---

### 5. Daily Events System

#### Processing Flow

1. **For each building with assigned workers:**
   - Get building type and professions
   - For each profession:
     - Filter workers assigned to that profession
     - Calculate events per worker: `max(1, base_events + reputation_bonus)`
       - If `base_events >= 2`: reduce by 1 (max 1)
       - Reputation bonus: `eval(bonus_formula) × 0.5` (reduced to 50%)
     - For each worker:
       - Check rebelliousness (if >80, 20% chance to refuse work)
         - On refusal: `rebelliousness -= comfort_level × 3`
       - Process N events (where N = events_per_worker)

2. **For each event:**
   - Select random story (weighted)
   - Select random skill from `skill_options`
   - Calculate `effective_skill` (with traits, equipment, libido)
   - Apply `difficulty_modifier` from story
   - **Roll:** `random(1, 100)`
   - **Determine outcome:**
     - Critical Success: `roll <= min(25, skill × 0.10)`
     - Success: `roll <= adjusted_skill`
     - Mediocre: `roll <= adjusted_skill + 10`
     - Failure: `roll > adjusted_skill + 10`
   - Calculate earnings based on outcome
   - Apply consequences (energy, health, joy, etc.)
   - Register in `daily_report`

3. **Calculate costs:**
   - Worker costs: `comfort_level × 20` per worker
   - Building costs: `base_costs + skill_bonus_cost`

4. **Random events:**
   - If there are active workers, chance for random event
   - Base probability + building level bonus

#### Outcomes and Modifiers

**Critical Success:**
- Earnings: `base × 0.65`
- Reputation: +10
- Energy: Less drain
- Joy: +2

**Success:**
- Earnings: `base × 0.75`
- Reputation: +5
- Energy: Normal drain
- Joy: +1

**Mediocre:**
- Earnings: `base × 0.75`
- Reputation: 0
- Energy: Normal drain
- Joy: 0

**Failure:**
- Earnings: `base × 2` (if negative) or -10
- Reputation: -5
- Energy: More drain
- Joy: -2
- Rebelliousness: +1

---

### 6. Buildings System

#### Structure

```json
{
    "id": "brothel",
    "name": "Brothel",
    "skill_name": "Hag Potions",
    "nsfw": true,
    "allowed_map_locations": ["tavern", "redhouse"],
    "professions": [
        {
            "id": "prostitute",
            "name": "Prostitute",
            "skills": ["Sex", "Anal", "BDSM", ...],
            "max_daily_workers": 3,
            "daily_story_count": {
                "base": 3,
                "bonus_formula": "reputation / 100"
            },
            "daily_stories": [...]
        }
    ]
}
```

#### Building Levels and Multipliers

**Only applies to random events, NOT daily earnings:**

- Level 1: 1.0x money, 1.0x reputation
- Level 2: 1.5x money, 1.3x reputation
- Level 3: 2.0x money, 1.6x reputation
- Level 4: 2.5x money, 1.9x reputation
- Level 5: 3.0x money, 2.2x reputation

**Formula:**
```python
money_multiplier = 1.0 + (level - 1) × 0.5  # Max 1.5x (capped)
reputation_multiplier = 1.0 + (level - 1) × 0.3
```

#### Building Costs

```python
# Base maintenance cost
base_cost = 100 × building_level

# Skill bonus cost (added during event processing)
skill_bonus_cost = (skill_bonus // 10) × 100

# Worker costs
comfort_costs = sum(comfort_level × 20 for each worker)
upkeep_costs = sum(
    (20 + 3 × level) if source == "recruited" else (5 + 1 × level)
    for each worker
)
worker_costs = comfort_costs + upkeep_costs

# Total daily cost
total_daily_cost = base_cost + skill_bonus_cost + worker_costs
```

---

### 7. Items System

#### Structure

```json
{
    "id": "item_id",
    "name": "Item Name",
    "type": "equipment|consumable|ingredient",
    "nsfw": false,
    "effect": {
        "skill_modifiers": {
            "Sex": 2,
            "Charm": 1
        },
        "health": 5,
        "energy": 10,
        "health_regeneration": 1,
        "libido": 5,
        "libido_regeneration": 2,
        "libido_max": 5
    },
    "price": 100,
    "description": "..."
}
```

#### Item Types

1. **Equipment:** Equipped, provides permanent bonuses while equipped
2. **Consumable:** Used once, immediate effect
3. **Ingredient:** For crafting/recipes

#### Inventory Format

```python
inventory = [
    (item_id, quantity, equipped),  # Tuple format
    # Example: ("sword", 1, True)  # 1 sword equipped
]
```

---

### 8. Skills System

#### Complete Skills List

**NSFW Skills:**
- Sex, Anal, BDSM, Hand, Oral, Homo, Special, Group, Extreme, Striptease

**SFW Skills:**
- Combat, Clever, Charm, Service, Agility, Craft

**Specialty Skills:**
- Specialty 4, Specialty 5, ..., Specialty 12 (reserved)

#### Image Search by Skill

The game searches for images using flexible patterns:

```python
skill_patterns = {
    "homo": ["les", "gay"],
    "service": ["wait", "service", "maid"],
    "special": ["special", "titty"],
    "striptease": ["strip", "striptease"]
}
# For other skills, searches directly by skill name
```

**Search priority:**
1. Worker folder + trait prefix + skill (e.g., `pregnant_sex.jpg`)
2. Worker folder + skill (e.g., `sex.jpg`)
3. Default folder + trait prefix + skill
4. Default folder + skill
5. Fallback to profile image

---

### 9. Libido System

#### Libido Regeneration

```python
base_regen = 1 + level
trait_bonus = sum(trait.libido_regeneration for traits)
item_bonus = sum(item.libido_regeneration for equipped items)
work_penalty = count_sexual_work_today(worker)  # -1 per sexual skill use

total_regen = base_regen + trait_bonus + item_bonus - work_penalty
total_regen = max(-2, total_regen)  # Minimum -2
```

**Sexual Skills that affect libido:**
Sex, Anal, BDSM, Hand, Oral, Homo, Special, Group, Extreme, Striptease

#### Libido Overflow

If `libido < 0` after regeneration:
- Overflow = `abs(negative_libido)`
- `rebelliousness += overflow`
- `libido = 0`

#### Max Libido

```python
base_max = 20
trait_bonus = sum(trait.libido_max for traits)
item_bonus = sum(item.libido_max for equipped items)
max_libido = base_max + trait_bonus + item_bonus
# Respects attribute_caps if they exist
```

---

### 10. Reputation System

#### Reputation Tiers

- 0-49: Unknown
- 50-99: New
- 100-199: Recognized
- 200-299: Respected
- 300-399: Well-Known
- 400-499: Popular
- 500-599: Famous
- 600-699: Highly Regarded
- 700-799: Prestigious
- 800-899: Elite
- 900+: Master

#### Reputation Bonus to Events

```python
bonus_events = eval(bonus_formula, {"reputation": reputation})
bonus_events = int(bonus_events × 0.5)  # Reduced to 50%

# Base events reduction: if base_events >= 2, reduce by 1
if base_events >= 2:
    base_events = max(1, base_events - 1)

events_per_worker = max(1, base_events + bonus_events)
```

---

### 11. Rebelliousness System

#### Effects

- **Rebelliousness > 80:** 20% chance to refuse work each day
- On refusal: `rebelliousness -= comfort_level × 3`

#### Rebelliousness Reduction

- On level up: `rebelliousness -= comfort_level`
- On skill up: `rebelliousness -= comfort_level`
- On work refusal: `rebelliousness -= comfort_level × 3` (reduction when refusing work)
- Traits can modify: `rebelliousness += trait.modifier`

#### Rebelliousness Caps

Some traits impose limits:
- "Obedient": cap at 40
- "Dependant": cap at 30
- "Meek": cap at 40

---

### 12. Comfort System

#### Comfort Level vs Comfort Desired

- **Comfort Level:** Current comfort level (1-5)
- **Comfort Desired:** Level the worker desires (1-5)

#### Daily Cost

```python
daily_cost = comfort_level × 20
```

#### Comfort Bonus

```python
comfort_bonus = max(0, comfort_level - comfort_desired)
joy_bonus = comfort_bonus  # Increases joy if comfort > desired
```

#### Minimum Relationship

```python
minimum_relationship = 10 + comfort_level
if relationship < minimum_relationship:
    relationship = minimum_relationship  # Enforced at start of each day
```

---

### 13. Random Events System

#### Trigger Conditions

- Only if there is at least one worker with active profession
- Base probability + building level bonus
- Formula: `max(base_probability, max_event_probability)`

#### Event Types

1. **Building Events:** Specific to building type
2. **Common Events:** General events
3. **Seasonal Events:** Seasonal events
4. **Shop Events:** Shop events

---

### 14. Resources System

#### Money

- **Income:** Sum of earnings from all events of the day
- **Expenses:** Building costs + worker costs (comfort × 20)
- **Net:** `total_income - total_costs`

#### Reputation

- **Gain:** +5 (Success), +10 (Critical Success)
- **Loss:** -5 (Failure)
- Affects bonus to daily events

---

### 15. Images System

#### Image Search

**For events:**
1. Search in `images/workers/{folder}/`
2. Patterns: `{trait_prefix}_{skill}.jpg`, `{skill}.jpg`
3. Fallback to `images/workers/default/`

**Trait Prefixes:**
- `pregnant_` - If has trait "Pregnant"
- `futa_` - If has trait "Futa"
- `transformed_` - If has trait "Transformed"
- `magical_` - If has trait "Magical"

**Outcome Images:**
- Success: `{skill}.jpg` or `{story_image}.jpg`
- Failure: `{skill}_failure.jpg` or `{failure_image}.jpg`
- Refused: `refuse.jpg` or `combat_failure.jpg`

---

### 16. JSON Data Structure

#### Workers JSON

```json
{
    "name": "Worker Name",
    "folder": "worker_folder",
    "gender": "female",
    "skills": {"Sex": 50, "Charm": 30, ...},
    "traits": ["Human", "Beautiful"],
    "cost": 1000,
    "unique": true,
    "encounter_only": true,
    "procedural": false,
    "monster": false,
    "nsfw": true,
    "description": "...",
    "comfort_desired": 3
}
```

#### Events JSON

```json
{
    "id": "event_id",
    "weight": 4,
    "report": "Event report",
    "difficulty_modifier": 5,
    "skill_options": ["Sex", "Charm"],
    "relevant_traits": ["Beautiful", "Charming"],
    "trait_bonus": "level * 100",
    "trait_success": "Client loves {worker_name}'s {trait}.",
    "earnings": {
        "success": "120 + skill * 5",
        "critical_success": "120 + skill * 10",
        "mediocre": "60 + skill * 2",
        "failure": "-10"
    },
    "consequences": {
        "success": {
            "energy": -1,
            "health": 0,
            "joy": 1,
            "reputation": 5
        }
    }
}
```

---

### 17. Key Formulas

#### Skill Roll Outcome

```python
roll = random(1, 100)
adjusted_skill = effective_skill + difficulty_modifier
crit_chance = min(25, max(1, int(0.10 × adjusted_skill)))

if roll <= crit_chance:
    outcome = "Critical Success"
elif roll <= adjusted_skill:
    outcome = "Success"
elif roll <= adjusted_skill + 10:
    outcome = "Mediocre"
else:
    outcome = "Failure"
```

#### Earnings Calculation

```python
# Base
base = eval(earnings_formula, {"skill": skill, "level": level})

# Outcome scaling
if outcome == "Critical Success":
    base *= 0.65
elif outcome == "Success":
    base *= 0.75
elif outcome == "Mediocre":
    base *= 0.75
else:  # Failure
    base = base × 2 if base < 0 else -10

# Trait bonus (50% chance, 30% scaling)
if random() < 0.5 and outcome in ["Success", "Critical Success"]:
    bonus = eval(trait_bonus, {"level": level}) × 0.3

# Trait multipliers
final = calculate_earnings(worker, base + bonus)
```

#### Health/Energy Regeneration

```python
# Health regen (at end of day)
health_regen = level + calculate_health_regeneration(worker)
# calculate_health_regeneration returns: 1 + sum(trait.health_regeneration for traits)
worker["health"] = min(max_health, worker["health"] + health_regen)

# Energy regen (at end of day)
energy_regen = level  # Base regeneration equals worker level
worker["energy"] = min(max_energy, worker["energy"] + energy_regen)
```

---

### 18. Game Flow

1. **Day Start:**
   - Advance calendar (`advance_date()`)
   - Reset building costs to 0
   - Recalculate max health/energy
   - Reset daily counters (failed_rolls, skill_uses)
   - Apply comfort bonuses to joy
   - Enforce minimum relationship (10 + comfort_level)

2. **Process Daily Events:**
   - `process_daily_events()` executes all events
   - For each building → profession → worker → event
   - Calculate earnings, apply consequences
   - Add skill_bonus_cost to building costs during processing
   - Generate `daily_report`

3. **Calculate Finances:**
   - Sum all earnings from daily_report
   - Calculate total costs (base_cost + skill_bonus_cost + worker_costs)
   - Net = income - costs

4. **Check Dead Workers:**
   - Workers with health <= 0 are removed

5. **Nightly Rest (Regeneration):**
   - Regenerate health: level + (1 + trait bonuses)
   - Regenerate energy: level + comfort bonus + trait bonuses
   - Regenerate libido (NSFW): considers same-day sexual work count

6. **Update Workers:**
   - Check level ups (success_count >= 20 × level)
   - Check skill ups (success_count >= 10 × skill)
   - Apply secondary attribute changes

7. **Random Events:**
   - Chance for random event (if workers active)
   - If triggered, show event

8. **Show Daily Report:**
   - Summary of all events of the day
   - Earnings, reputation, attribute changes

---

### 19. Important Constants

- **SKILL_MAX:** 100 (base skills cap)
- **Max Earnings Multiplier:** 1.6x (total multiplier cap)
- **Per-Trait Earnings Cap:** 1.15x (individual trait cap)
- **Level Up Threshold:** 20 × current_level successes
- **Skill Up Threshold:** 10 × current_skill successes
- **Rebelliousness Refuse Threshold:** >80 (20% chance)
- **Libido Base Max:** 20
- **Health Base:** 10 + (level × 5)
- **Energy Base:** level × 5
- **Health Regen:** level + (1 + trait bonuses)
- **Energy Regen:** level per day
- **Comfort Cost:** comfort_level × 20 per day per worker
- **Worker Upkeep (Recruited):** 20 + (3 × level) per day
- **Worker Upkeep (Bought):** 5 + (1 × level) per day
- **Base Building Cost:** 100 × building_level per day
- **Skill Bonus Cost:** (skill_bonus // 10) × 100 per day
- **Minimum Relationship:** 10 + comfort_level

---

### 20. Implementation Notes

- The game uses Ren'Py as engine
- Data is saved in JSON
- Images are searched dynamically by name
- The traits system is extensible (new traits can be added)
- Events use evaluable formulas for flexibility
- The skills system allows exceeding 100 with modifiers
- Workers can be unique, procedural, or monsters
- The NSFW system can be disabled (filters content)

---

## 📝 Quick References

### NSFW Skills
Sex, Anal, BDSM, Hand, Oral, Homo, Special, Group, Extreme, Striptease

### SFW Skills
Combat, Clever, Charm, Service, Agility, Craft

### Secondary Attributes
health, energy, joy, rebelliousness, romance, relationship, libido, comfort_level, comfort_desired

### Outcomes
Critical Success, Success, Mediocre, Failure

### Worker Types
unique, procedural, encounter_only, monster

### Item Types
equipment, consumable, ingredient

---
