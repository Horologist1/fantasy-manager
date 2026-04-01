# Interaction templates

- Training-oriented sample: `training_interaction.sample.json` (includes `training_skill`, `training_results`, `trait_chance` inside results, branch images, etc.).
- Intro copy helper: `training_intro_sequences.sample.json` (narration strings only; not a full interaction schema).

## Manager vs worker gender

- **`gender_filter`**: restricts the interaction to the **manager** (Lord/Lady). Use `male`, `female`, or aliases `lord`, `lady` (normalized the same way as random events). Runtime: **Lord** title → canonical `male`, otherwise `female`, then compared to the normalized filter.
- **`worker_gender`**: restricts to the **selected worker’s** `gender` string (worker data), same as elsewhere in content.

Random **events** and **daily stories** use **`player_gender_requirement`** for the same manager-side rule; interactions keep the historical name **`gender_filter`**.

Schema: `docs/json_schema_canonical.md` (Interactions) and `game/data/json_schema_standard.md`.
