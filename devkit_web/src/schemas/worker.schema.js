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
    // Procedural monster templates are identified by template_id and intentionally
    // have no display name; every instantiated worker still needs one.
    name: { type: 'string', unique_in_file: true },
    folder: { type: 'string', catalog: 'all_worker_folders' },
    cost: { type: 'int', min: 0 },
    nsfw: { type: 'bool' },
    unique: { type: 'bool' },
    encounter_only: { type: 'bool' },
    monster: { type: 'bool' },
    procedural: { type: 'bool' },
    recruit_only: { type: 'bool' },        // excluded from the buy-workers shop; obtainable only via recruit events
    recruitment_locked: { type: 'bool' },  // held out of the recruit pool (quest/story workers, e.g. Yvara, The Lanista)
    event_recruit_only: { type: 'bool' },
    required_store_value: {
      type: ['list_of_objects', 'object', 'null'],
      item_fields: {
        var: { type: 'string', required: true },
        equals: { type: ['string', 'bool', 'int', 'float', 'null'] },
      },
      fields: {
        var: { type: 'string', required: true },
        equals: { type: ['string', 'bool', 'int', 'float', 'null'] },
      },
    },
    skills: { type: 'dict_of_numbers' },
    names_list: { type: ['string', 'null'], catalog: 'names_lists' },
    traits: { type: 'list_of_strings', catalog: 'all_traits' },
    description: { type: ['longtext', 'null'] },
    gender: { type: 'enum', options: ['male', 'female'] },
    comfort_desired: { type: 'int', min: 1, max: 5 },
    template_id: { type: ['string', 'null'] },
    procedural_template: { type: 'bool' },
    monster_archetype: { type: ['string', 'null'] },
    monster_secondary_traits: { type: 'list_of_strings', catalog: 'all_traits' },
  },
  rules: [
    {
      id: 'worker_identity',
      check: (e) => e.procedural_template
        ? typeof e.template_id === 'string' && e.template_id.length > 0
        : typeof e.name === 'string' && e.name.length > 0,
      severity: 'error',
      message: 'workers need name; procedural monster templates need template_id',
    },
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
      id: 'spawnable_needs_names_list',
      // The game clones every non-unique worker as a procedural recruit and
      // draws the clone's name from names_list. A template without a pool used
      // to put a servant literally called "Unknown" on the roster. Uniques are
      // never cloned, so they may leave it empty.
      check: (e) => !!e.unique || (e.names_list && e.names_list.length > 0),
      severity: 'warning',
      message: 'Non-unique workers are spawn templates and should set names_list',
    },
    {
      id: 'skills_complete',
      check: (e) => e.procedural || ALL_SKILLS.every((s) => s in (e.skills || {})),
      severity: 'warning',
      message: `skills should include all 25 canonical keys (${ALL_SKILLS.join(', ')}). Procedural workers are exempt. Scripted story workers (e.g. Yvara) may legitimately omit Specialty 4–12 slots — this is a warning, not a blocking error.`,
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
