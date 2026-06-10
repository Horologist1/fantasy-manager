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
      hint: 'Must match images/workers/<folder>/',
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
