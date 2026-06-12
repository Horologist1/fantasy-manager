// Worker recipes beyond unique_worker — monster and procedural template.
import { ALL_SKILLS } from '../schemas/worker.schema.js';

function flatSkills(level) {
  return Object.fromEntries(ALL_SKILLS.map((s) => [s, level]));
}

export const monster_worker_recipe = {
  id: 'monster_worker',
  title: 'Monster Worker',
  description: 'An encounter-only monster (captured via events/loot, like Amanita or Moss).',
  kind: 'worker',
  default_output: 'workers/workers_<modname>_monsters.json',
  steps: [
    { id: 'name', type: 'string', label: 'Monster name', required: true },
    {
      id: 'folder', type: 'string', label: 'Image folder name', catalog: 'image_folders',
      hint: 'Pick an existing folder under images/workers/ — or type a new name.',
      required: true,
    },
    { id: 'gender', type: 'enum', label: 'Gender', options: ['female', 'male'], default: 'female' },
    {
      id: 'race', type: 'enum', label: 'Race trait',
      options: ['Transformed', 'Demon', 'Orc', 'Goblin', 'Vampire'],
      option_descriptions: {
        Transformed: 'Generic non-human creature.',
        Demon: 'Powerful but socially difficult.',
        Orc: 'Strong and combat-oriented.',
        Goblin: 'Crafty, lower stats overall.',
        Vampire: 'Nocturnal with special daily effects.',
      },
      default: 'Transformed',
    },
    { id: 'extra_traits', type: 'list_of_strings', label: 'Additional traits',
      catalog: 'all_traits', default: [] },
    { id: 'combat_level', type: 'int', label: 'Combat skill', default: 45, min: 0, max: 100 },
    { id: 'description', type: 'longtext', label: 'Description' },
    { id: 'nsfw', type: 'bool', label: 'NSFW content?', default: true },
  ],
  build: (a) => {
    const skills = flatSkills(20);
    skills.Combat = a.combat_level ?? 45;
    return {
      name: a.name,
      folder: a.folder,
      cost: 0,
      nsfw: !!a.nsfw,
      unique: false,
      encounter_only: true,
      monster: true,
      procedural: false,
      skills,
      names_list: null,
      traits: [a.race, ...(a.extra_traits || [])].filter(Boolean),
      description: a.description || null,
      gender: a.gender,
      comfort_desired: 1,
    };
  },
};

export const procedural_worker_template_recipe = {
  id: 'procedural_worker_template',
  title: 'Procedural Worker Template',
  description: 'A hireable worker template: the game spawns copies with random names from a names list.',
  kind: 'worker',
  default_output: 'workers/workers_<modname>_procedural.json',
  steps: [
    { id: 'name', type: 'string', label: 'Template name', required: true,
      hint: 'Internal name for the template, e.g. "Village Cook".' },
    {
      id: 'folder', type: 'string', label: 'Image folder name', catalog: 'image_folders',
      hint: 'Pick an existing folder under images/workers/ — or type a new name.',
      required: true,
    },
    { id: 'gender', type: 'enum', label: 'Gender', options: ['female', 'male'], default: 'female' },
    {
      id: 'names_list', type: 'enum', label: 'Random names list', required: true,
      options: (ctx) => Array.from(ctx.catalogs?.names_lists || []).sort(),
      hint: 'Spawned copies draw their names from this list (data/names.json).',
    },
    {
      id: 'race', type: 'enum', label: 'Race',
      options: ['Human', 'Elf', 'Dwarf', 'Demon', 'Angel', 'Vampire', 'Orc', 'Goblin'],
      default: 'Human',
    },
    { id: 'extra_traits', type: 'list_of_strings', label: 'Additional traits',
      catalog: 'all_traits', default: [] },
    { id: 'cost', type: 'int', label: 'Daily cost', default: 1100, min: 0 },
    { id: 'skill_level', type: 'int', label: 'Base skill level', default: 25, min: 0, max: 100 },
    { id: 'description', type: 'longtext', label: 'Description' },
    { id: 'nsfw', type: 'bool', label: 'NSFW content?', default: false },
  ],
  build: (a) => ({
    name: a.name,
    folder: a.folder,
    cost: a.cost ?? 1100,
    nsfw: !!a.nsfw,
    unique: false,
    encounter_only: false,
    monster: false,
    procedural: true,
    skills: flatSkills(a.skill_level ?? 25),
    names_list: a.names_list,
    traits: [a.race, ...(a.extra_traits || [])].filter(Boolean),
    description: a.description || null,
    gender: a.gender,
    comfort_desired: 3,
  }),
};
