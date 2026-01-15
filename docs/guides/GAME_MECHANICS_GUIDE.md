# Fantasy Manager - Complete Game Mechanics Guide

## Table of Contents
1. [Core Game Loop](#core-game-loop)
2. [Worker Management](#worker-management)
3. [Building System](#building-system)
4. [Economic System](#economic-system)
5. [Success Probability & Earnings](#success-probability--earnings)
6. [Traits & Equipment](#traits--equipment)
7. [Interactions System](#interactions-system)
8. [Events & Random Encounters](#events--random-encounters)
9. [Progression & Leveling](#progression--leveling)
10. [Balance Changes Summary](#balance-changes-summary)

---

## Core Game Loop

### Daily Cycle
1. **Start of Day**: Date advances, energy/health regenerate
2. **Worker Processing**: Assigned workers perform their jobs
3. **Income Calculation**: Sum all earnings from daily stories
4. **Cost Deduction**: Building maintenance + worker upkeep
5. **Random Events**: 50% chance for special events (if workers active)
6. **End of Day**: Display daily report, check game over conditions

### Game Over Condition
- Money falls below -$5000

---

## Worker Management

### Worker Types
- **Bought Workers**: Purchased from market, lower upkeep costs
- **Recruited Workers**: Found through events, higher upkeep costs
- **Monster Workers**: Special creatures with unique abilities

### Worker Stats
- **Level**: Affects health, energy, and various bonuses (starts at 1)
- **Health**: 10 + (level × 5) + trait bonuses
- **Energy**: Level × 5 + trait bonuses (regenerates level per day)
- **Skills**: 0-100 base, can exceed with bonuses from traits/equipment/libido

### Secondary Attributes
- **Joy** (0-100): Worker happiness, affects performance
- **Rebelliousness** (0-100): Resistance to work, >80 = 20% chance to refuse
- **Romance** (0-100): Romantic attraction to player
- **Relationship** (0-100): General trust and friendship (minimum: 10 + comfort_level)
- **Comfort Level** (1-5): Current accommodation quality
- **Comfort Desired** (1-5): Preferred accommodation level
- **Libido** (0-dynamic max): Sexual energy, affects sexual skills

### Libido System (NSFW Mode)
- **Base Maximum**: 20
- **Dynamic Maximum**: Base + trait bonuses + item bonuses
- **Regeneration**: 1 + level + trait/item bonuses - sexual_work_count per day
  - Minimum regeneration: -2 (can decrease if overworked)
- **Skill Bonus**: Sexual skills gain floor(libido/2) bonus
- **Overflow**: Negative libido converts to rebelliousness

---

## Building System

### Building Types
1. **Brothel** (NSFW): Prostitute, Stripper, Service
2. **Restaurant**: Service, Cook
3. **Adventurer's Guild**: Adventurer, Monster Capture
4. **Tavern**: Bartender, Performer
5. **Casino**: Dealer, Guard

### Building Mechanics
- **Base Level**: 1-5 (affects capacity and bonuses)
- **Skill**: Base level × 10 (affects event success)
- **Reputation**: 0-1000 (affects story frequency)
- **Capacity**: Max workers = base + (level - 1) for most professions

### Daily Costs
- **Base Maintenance**: 100 × building level
- **Worker Comfort**: 20 × comfort_level per assigned worker
- **Worker Upkeep**: 
  - Recruited: 20 + (3 × level) per day
  - Bought: 5 + (1 × level) per day
- **Skill Bonus Cost**: floor(skill_bonus/10) × 100

---

## Economic System

### Income Sources
- **Daily Stories**: Workers perform jobs based on profession
- **Random Events**: Special scenarios with monetary rewards
- **Item Sales**: Selling loot and equipment

### Cost Structure
- **Building Maintenance**: Fixed daily costs
- **Worker Upkeep**: Based on worker source and level
- **Interaction Costs**: Player actions with workers
- **Item Purchases**: Equipment and consumables

### Profitability Examples (Typical Worker, Skill 20)
- **Early Game** (Level 1 building, comfort 1):
  - Income: ~180-260/day per worker
  - Costs: ~160-220/day per worker
  - **Net Margin**: 40-80/day per worker

- **Mid Game** (Level 3 building, comfort 3):
  - Income: ~350-500/day per worker
  - Costs: ~250-350/day per worker
  - **Net Margin**: 100-180/day per worker

---

## Success Probability & Earnings

### Success Formula
```
adjusted_skill = effective_skill + difficulty_modifier
```

### Probability Thresholds (New Balanced System)
- **Critical Success**: ≤ min(25%, 10% of adjusted_skill)
- **Success**: ≤ adjusted_skill (with reserved space for mediocre/failure)
- **Mediocre**: Guaranteed ≥10% chance
- **Failure**: Guaranteed ≥1% chance

### Earnings Calculation
1. **Base Formula**: Evaluated from story (e.g., "80 + skill * 3")
2. **Trait Bonuses**: Added before multipliers (reduced to 30% of calculated)
3. **Trait Multipliers**: Applied with caps (per-trait ≤1.15, total ≤1.6)
4. **Outcome Scaling**: Final adjustment by result type
   - Critical Success: ×0.65
   - Success: ×0.75
   - Mediocre: ×0.75
   - Failure: ×2 penalty (minimum -10 if originally 0)

### Story Volume
- **Base Stories**: Defined per profession (reduced by 1 if originally ≥2)
- **Reputation Bonus**: Formula-based (e.g., "reputation / 100"), then reduced to 50% of calculated value
- **Per Worker**: Each assigned worker gets full story allocation (base_events + bonus_events)

---

## Traits & Equipment

### Trait Categories
- **Racial**: Human, Elf, Dwarf, Orc, Ogre, Demon, Angel, Goblin
- **Physical**: Beautiful, Strong, Flexible, body-specific traits
- **Mental**: Clever, Wise, Quick Learner, personality traits
- **Social**: Charming, Elegant, Smooth Talker
- **Special**: Mystical, Transformed, temporary conditions

### Trait Effects
- **Skill Modifiers**: Flat bonuses to specific skills
- **Earnings Multipliers**: 1.05-1.15 range (capped at 1.15 per trait, 1.6 total)
- **Attribute Modifiers**: Health, energy, libido, secondary stats
- **Caps/Minimums**: Enforce attribute limits
- **Conflicts**: Mutually exclusive traits

### Equipment System
- **Types**: Weapon, Armor, Accessory, Consumable
- **Effects**: Skill bonuses, health/energy, special abilities
- **Durability**: Equipment degrades with use (weapons/armor)
- **Libido Items**: Can increase max libido and regeneration

### Libido Enhancement Items
- **Amulet of Desire**: +5 max libido, +2 regeneration (260 gold)
- **Elixir of Passion**: +10 libido, +3 regeneration (1000 gold, rare)
  - Only available in Elite Emporium (shop 3)
  - 15% daily availability chance
  - Very rare loot drop (0.02 weight)

---

## Interactions System

### Interaction Categories
1. **Discipline**: Training and correction (reduces rebelliousness)
2. **Romance**: Building romantic relationships
3. **Friendship**: Developing trust and loyalty
4. **Joy**: Entertainment and happiness activities

### Progression Chains
- **Basic → Advanced → Elite**: Each category has escalating interactions
- **Requirements**: Previous interactions unlock next tier
- **Cooldowns**: Prevent spam, vary by interaction intensity
- **Usage Limits**: Some powerful interactions have use caps

### Costs
- **Energy**: 1-4 points from player
- **Money**: 0-100+ depending on interaction
- **Health**: Some interactions cost health

---

## Events & Random Encounters

### Event Types
- **Daily Stories**: Regular work activities (automatic)
- **Random Events**: Special scenarios (50% daily chance)
- **Recruitment Events**: Finding new workers
- **Building Events**: Location-specific scenarios

### Event Mechanics
- **Conditions**: When events can trigger
- **Worker Selection**: Random, choose, or none
- **Skill Checks**: Success based on worker abilities
- **Multiple Choices**: Player decisions affect outcomes
- **Consequences**: Money, reputation, worker stats, items

### Building Multipliers (Random Events Only)
- **Money**: 1.0x + (level-1) × 0.5 (capped at 1.5x)
- **Reputation**: 1.0x + (level-1) × 0.3
- **Note**: Does NOT affect daily worker earnings

---

## Progression & Leveling

### Worker Leveling
- **Experience**: Success count tracks achievements
- **Threshold**: 20 successes per level
- **Benefits**: +5 health, +5 energy, improved regeneration
- **Skill Growth**: Through use and training

### Building Progression
- **Skill Points**: Earned through successful operations
- **Level Benefits**: More capacity, better success rates
- **Reputation**: Affects story frequency and client quality
- **Upgrades**: Unlock new professions and capabilities

### Economic Progression
- **Early Game**: Focus on basic professions, manage costs carefully
- **Mid Game**: Expand building capacity, optimize worker assignments
- **Late Game**: High-skill workers, premium services, rare events

---

## Balance Changes Summary

### Recent Adjustments (Applied)
1. **Probability Floors**: Minimum 1% failure, 10% mediocre
2. **Earnings Reduction**: 20-35% across all stories via outcome scaling
3. **Trait Balance**: Multipliers capped, bonuses reduced
4. **Cost Increases**: Comfort costs doubled, upkeep differentiated by source
5. **Volume Reduction**: Fewer base stories, softer reputation bonus
6. **Libido Rebalance**: floor(libido/2) bonus, dynamic maximums

### Design Goals
- **Prevent Snowballing**: Early advantages don't become overwhelming
- **Meaningful Choices**: Different worker types have distinct economics
- **Progression Curve**: Steady growth without exploitation
- **Risk/Reward**: Failure has real consequences
- **Player Agency**: Strategic decisions matter

---

## Tips for Players

### Starting Strategy
1. Buy 2-3 workers with complementary skills
2. Focus on one building type initially
3. Manage comfort levels vs. costs carefully
4. Use interactions to maintain worker loyalty

### Economic Management
- Monitor daily profit margins per worker
- Upgrade buildings when you can afford the increased capacity
- Balance high-skill expensive workers with cheaper reliable ones
- Save money for recruitment opportunities and rare items

### Worker Optimization
- Match worker skills to profession requirements
- Use traits strategically for earnings multipliers
- Equip items that complement worker strengths
- Maintain good relationships to prevent rebelliousness

### Advanced Play
- Plan for trait combinations and synergies
- Time recruitment for optimal worker availability
- Stockpile rare items and consumables
- Build reputation for increased story frequency

---

*This guide reflects the current game balance as of the latest updates. Mechanics may continue to evolve based on player feedback and testing.*
