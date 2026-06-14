// Trait recipes — permanent and temporary traits.

function traitSteps() {
  return [
    { id: 'name', type: 'string', label: 'Trait name', required: true,
      hint: 'e.g. Battle-Hardened' },
    { id: 'description', type: 'longtext', label: 'Description',
      hint: 'Shown in the worker detail panel.' },
    { id: 'skill_modifiers', type: 'dict_of_numbers', key_catalog: 'all_skills',
      label: 'Skill bonuses / penalties',
      hint: 'Click a skill to add it, then set the modifier (e.g. Combat +5).' },
    { id: 'earnings_multiplier', type: 'float', label: 'Earnings multiplier', default: 0,
      hint: '0 = no change. 1.2 = worker earns +20%. 0.8 = -20%.' },
    { id: 'conflicts', type: 'list_of_strings', catalog: 'all_traits',
      label: 'Conflicting traits',
      hint: 'A worker can never have this trait and a conflicting one at the same time.',
      default: [] },
    { id: 'nsfw', type: 'bool', label: 'NSFW trait?', default: false },
  ];
}

function buildTrait(a, { duration = null } = {}) {
  const t = {
    name: a.name,
    conflicts: a.conflicts || [],
    removes_traits: [],
    modifiers: {
      skill_modifiers: a.skill_modifiers || {},
      attribute_caps: {},
      attribute_minimums: {},
      daily_effects: {},
      earnings_multiplier: a.earnings_multiplier || 0,
      libido_max: 0,
      libido_regeneration: 0,
    },
    description: a.description || null,
    nsfw: !!a.nsfw,
  };
  if (duration != null) t.duration = duration;
  return t;
}

export const permanent_trait_recipe = {
  id: 'permanent_trait',
  title: 'Permanent Trait',
  description: 'A trait that stays on the worker until removed by an event or item.',
  kind: 'trait',
  default_output: 'traits/traits_<modname>.json',
  steps: traitSteps(),
  build: (a) => buildTrait(a),
};

export const temporary_trait_recipe = {
  id: 'temporary_trait',
  title: 'Temporary Trait',
  description: 'A trait that expires after a number of days (good for buffs, injuries, moods).',
  kind: 'trait',
  default_output: 'traits/traits_<modname>.json',
  steps: [
    ...traitSteps(),
    { id: 'duration', type: 'int', label: 'Duration (days)', default: 3, min: 1,
      hint: 'Days before the trait expires on its own.' },
  ],
  build: (a) => buildTrait(a, { duration: a.duration || 3 }),
};
