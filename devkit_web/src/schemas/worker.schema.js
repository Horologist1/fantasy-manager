export const ALL_SKILLS = [
  'Sex', 'Anal', 'BDSM', 'Hand', 'Oral', 'Homo', 'Special', 'Group',
  'Extreme', 'Striptease', 'Combat', 'Clever', 'Charm', 'Service',
  'Agility', 'Craft',
  'Specialty 4', 'Specialty 5', 'Specialty 6', 'Specialty 7', 'Specialty 8',
  'Specialty 9', 'Specialty 10', 'Specialty 11', 'Specialty 12',
];

export const RACE_TRAITS = [
  'Human', 'Elf', 'Dwarf', 'Demon', 'Angel', 'Vampire', 'Orc', 'Goblin', 'Transformed',
];

export const worker_schema = {
  id: 'worker',
  fields: {
    name: { type: 'string', required: true, unique_in_file: true },
    folder: { type: 'string', catalog: 'all_worker_folders' },
    cost: { type: 'int', min: 0 },
    nsfw: { type: 'bool' },
    unique: { type: 'bool' },
    encounter_only: { type: 'bool' },
    monster: { type: 'bool' },
    procedural: { type: 'bool' },
    skills: { type: 'dict_of_numbers' },
    names_list: { type: ['string', 'null'], catalog: 'names_lists' },
    traits: { type: 'list_of_strings', catalog: 'all_traits' },
    description: { type: ['longtext', 'null'] },
    gender: { type: 'enum', options: ['male', 'female'] },
    comfort_desired: { type: 'int', min: 1, max: 5 },
    template_id: { type: ['string', 'null'] },
  },
  rules: [
    {
      id: 'traits_exist',
      check: (e, ctx) =>
        (e.traits || []).every((t) => ctx.catalogs.all_traits.has(t)),
      severity: 'error',
      message: 'One or more traits do not exist in any traits file',
    },
    {
      id: 'race_trait_present',
      check: (e, ctx) =>
        (e.traits || []).some((t) => ctx.catalogs.race_traits.has(t)),
      severity: 'warning',
      message: 'Worker has no race trait (Human, Elf, Orc, …)',
    },
    {
      id: 'procedural_needs_names_list',
      check: (e) => !e.procedural || (e.names_list && e.names_list.length > 0),
      severity: 'warning',
      message: 'Procedural workers should set names_list',
    },
    {
      id: 'skills_complete',
      check: (e) => ALL_SKILLS.every((s) => s in (e.skills || {})),
      severity: 'error',
      message: `skills must include all 25 canonical keys (${ALL_SKILLS.join(', ')})`,
    },
    {
      id: 'cost_in_range',
      check: (e) => e.cost >= 0 && e.cost <= 5000,
      severity: 'warning',
      message: 'cost unusually high (>5000); most workers are 1000–1500',
    },
  ],
  legacy: {},
};
