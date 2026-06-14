import { ALL_SKILLS } from '../schemas/worker.schema.js';

const SKILL_PRESETS = {
  balanced: () => Object.fromEntries(ALL_SKILLS.map((s) => [s, 25])),
  combat: () => {
    const base = Object.fromEntries(ALL_SKILLS.map((s) => [s, 22]));
    base.Combat = 45;
    base.Agility = 40;
    base.Service = 30;
    return base;
  },
  magic: () => {
    const base = Object.fromEntries(ALL_SKILLS.map((s) => [s, 22]));
    base.Craft = 45;
    base.Clever = 40;
    return base;
  },
  social: () => {
    const base = Object.fromEntries(ALL_SKILLS.map((s) => [s, 25]));
    base.Charm = 45;
    base.Striptease = 38;
    base.Service = 35;
    return base;
  },
  service: () => {
    const base = Object.fromEntries(ALL_SKILLS.map((s) => [s, 25]));
    base.Service = 45;
    base.Craft = 35;
    return base;
  },
};

export const unique_worker_recipe = {
  id: 'unique_worker',
  title: 'Unique Worker',
  description: 'A named worker with a fixed image folder (Aelis/Yvara style).',
  default_output: 'workers/workers_<modname>_unique.json',
  steps: [
    { id: 'name', type: 'string', label: 'Worker name', required: true },
    {
      id: 'folder',
      type: 'string',
      label: 'Image folder name',
      catalog: 'image_folders',
      hint: 'Pick an existing folder under images/workers/ — or type a new name (you can add images later).',
      required: true,
    },
    { id: 'nsfw', type: 'bool', label: 'NSFW content?', default: false },
    {
      id: 'gender',
      type: 'enum',
      label: 'Gender',
      options: ['female', 'male'],
      default: 'female',
    },
    {
      id: 'race',
      type: 'enum',
      label: 'Race',
      options: ['Human', 'Elf', 'Dwarf', 'Demon', 'Angel', 'Vampire', 'Orc', 'Goblin', 'Transformed'],
      option_descriptions: {
        Human: 'Baseline race. No special bonuses or penalties.',
        Elf: 'Long-lived, agile, often magical. See traits_races.json for stat modifiers.',
        Dwarf: 'Sturdy and craft-oriented. See traits_races.json for stat modifiers.',
        Demon: 'Powerful but socially difficult. NSFW-leaning. See traits_races.json for modifiers.',
        Angel: 'Charismatic and pure. See traits_races.json for modifiers.',
        Vampire: 'Nocturnal, NSFW-leaning, special daily effects. See traits_races.json.',
        Orc: 'Strong and combat-oriented, weaker social skills. See traits_races.json.',
        Goblin: 'Crafty and resourceful, lower stats overall. See traits_races.json.',
        Transformed: 'For worker that is not natively human — set when WM-style "Not Human" trait applies.',
      },
      default: 'Human',
      required: true,
    },
    {
      id: 'extra_traits',
      type: 'list_of_strings',
      label: 'Additional traits',
      catalog: 'all_traits',
      default: [],
    },
    {
      id: 'skill_focus',
      type: 'enum',
      label: 'Skill focus',
      options: ['balanced', 'combat', 'magic', 'social', 'service'],
      option_descriptions: {
        balanced: 'All 25 skills set to 25. Generic worker, no specialty.',
        combat: 'Combat 45, Agility 40, Service 30, all other skills 22. Use for fighters / arena workers.',
        magic: 'Craft 45, Clever 40, all others 22. Use for mages / library / arcane workers.',
        social: 'Charm 45, Striptease 38, Service 35, all others 25. Use for hostesses / entertainers.',
        service: 'Service 45, Craft 35, all others 25. Use for maids / cooks / shop workers.',
      },
      default: 'balanced',
    },
    { id: 'description', type: 'longtext', label: 'Description' },
  ],
  build: (a) => ({
    name: a.name,
    folder: a.folder,
    cost: 1300,
    nsfw: !!a.nsfw,
    unique: true,
    encounter_only: true,
    monster: false,
    procedural: false,
    skills: (SKILL_PRESETS[a.skill_focus] || SKILL_PRESETS.balanced)(),
    names_list: null,
    traits: [a.race, ...(a.extra_traits || [])].filter(Boolean),
    description: a.description || null,
    gender: a.gender,
    comfort_desired: 3,
  }),
};
