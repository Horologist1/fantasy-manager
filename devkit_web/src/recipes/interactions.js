// Interaction recipes — simple, trait-granting, worker-specific.
import { slug } from './_helpers.js';

const EFFECTS_STEP = {
  id: 'effects',
  type: 'object',
  label: 'Effects on the worker',
  fields: {
    joy: { type: 'int', label: 'Joy' },
    relationship: { type: 'int', label: 'Relationship' },
    romance: { type: 'int', label: 'Romance' },
    rebelliousness: { type: 'int', label: 'Rebelliousness' },
    libido: { type: 'int', label: 'Libido (NSFW)' },
  },
};

const GENDER_STEP = {
  id: 'worker_gender', type: 'enum', label: 'Worker gender',
  options: ['any', 'female', 'male'], default: 'any',
};

function baseInteraction(a) {
  return {
    id: slug(a.name),
    name: a.name,
    description: a.description || null,
    interaction_level: a.interaction_level ?? 1,
    interaction_type: null,
    cost_energy: a.cost_energy ?? 0,
    cost_money: a.cost_money ?? 0,
    effect: {
      romance: a.effects?.romance ?? 0,
      relationship: a.effects?.relationship ?? 0,
      joy: a.effects?.joy ?? 0,
      rebelliousness: a.effects?.rebelliousness ?? 0,
      libido: a.effects?.libido ?? 0,
      flags: {},
      add_trait: null,
      remove_trait: null,
    },
    gender_filter: null,
    worker_gender: a.worker_gender === 'any' || !a.worker_gender ? null : a.worker_gender,
    categories: a.categories || [],
    image: null,
    nsfw: !!a.nsfw,
    stat_requirements: {},
    specific_workers: [],
    specific_worker_images: [],
    required_traits: a.required_traits || [],
    excluded_traits: a.excluded_traits || [],
    required_flags: {},
    excluded_flags: {},
  };
}

export const simple_interaction_recipe = {
  id: 'simple_interaction',
  title: 'Simple Interaction',
  description: 'A talk/activity option in the worker interaction menu with stat effects.',
  kind: 'interaction',
  default_output: 'interactions/interactions_<modname>.json',
  steps: [
    { id: 'name', type: 'string', label: 'Interaction name', required: true,
      hint: 'e.g. Evening Stroll' },
    { id: 'description', type: 'longtext', label: 'Narration text', required: true,
      hint: 'What happens when the player picks this interaction.' },
    { id: 'categories', type: 'list_of_strings', label: 'Categories', default: [],
      hint: 'Menu groups, e.g. Friendship, Romance, Discipline, Special.' },
    { id: 'cost_energy', type: 'int', label: 'Energy cost (manager)', default: 5, min: 0 },
    { id: 'cost_money', type: 'int', label: 'Money cost', default: 0, min: 0 },
    EFFECTS_STEP,
    GENDER_STEP,
    { id: 'nsfw', type: 'bool', label: 'NSFW interaction?', default: false },
  ],
  build: (a) => baseInteraction(a),
};

export const trait_granting_interaction_recipe = {
  id: 'trait_granting_interaction',
  title: 'Trait-Granting Interaction',
  description: 'An interaction that adds a trait to the worker (training, gift, ritual…).',
  kind: 'interaction',
  default_output: 'interactions/interactions_<modname>.json',
  steps: [
    { id: 'name', type: 'string', label: 'Interaction name', required: true },
    { id: 'description', type: 'longtext', label: 'Narration text', required: true },
    { id: 'trait', type: 'list_of_strings', catalog: 'all_traits', label: 'Trait to grant',
      required: true, hint: 'Pick exactly one trait.' },
    { id: 'duration', type: 'int', label: 'Trait duration (days)', default: 0, min: 0,
      hint: '0 = use the trait’s own duration (permanent if it has none).' },
    { id: 'cost_energy', type: 'int', label: 'Energy cost (manager)', default: 10, min: 0 },
    { id: 'required_traits', type: 'list_of_strings', catalog: 'all_traits',
      label: 'Worker must have these traits', default: [] },
    GENDER_STEP,
    { id: 'nsfw', type: 'bool', label: 'NSFW interaction?', default: false },
  ],
  build: (a) => {
    const granted = (a.trait || [])[0] || null;
    const i = baseInteraction(a);
    i.effect.add_trait = granted ? { name: granted, duration: a.duration || 0 } : null;
    // Hide the interaction once the worker already has the trait.
    i.excluded_traits = granted ? [granted] : [];
    return i;
  },
};

export const worker_specific_interaction_recipe = {
  id: 'worker_specific_interaction',
  title: 'Worker-Specific Interaction',
  description: 'An interaction only available for specific named workers (Aelis, Yvara, your own…).',
  kind: 'interaction',
  default_output: 'interactions/interactions_<modname>.json',
  steps: [
    { id: 'name', type: 'string', label: 'Interaction name', required: true },
    { id: 'description', type: 'longtext', label: 'Narration text', required: true },
    { id: 'specific_workers', type: 'list_of_strings', catalog: 'all_worker_names',
      label: 'Workers who get this interaction', required: true },
    { id: 'cost_energy', type: 'int', label: 'Energy cost (manager)', default: 5, min: 0 },
    EFFECTS_STEP,
    { id: 'nsfw', type: 'bool', label: 'NSFW interaction?', default: false },
  ],
  build: (a) => {
    const i = baseInteraction(a);
    i.specific_workers = a.specific_workers || [];
    return i;
  },
};
