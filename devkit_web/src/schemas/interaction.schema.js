// Interaction schema — game/data/interactions/*.json (array files, appended).
import { allIn } from './_rules.js';

export const interaction_schema = {
  id: 'interaction',
  fields: {
    id: { type: 'string', required: true, unique_in_file: true },
    name: { type: 'string', required: true },
    description: { type: ['longtext', 'null'] },
    interaction_level: { type: ['int', 'null'] },
    interaction_type: { type: ['string', 'null'] },
    cost_energy: { type: 'int' },
    cost_money: { type: 'int' },
    cost_health: { type: 'int' },
    effect: {
      type: 'object',
      fields: {
        romance: { type: 'float' },
        relationship: { type: 'float' },
        joy: { type: 'float' },
        rebelliousness: { type: 'float' },
        libido: { type: 'float' },
        flags: { type: 'dict_of_objects' },
        trait_remove_chance: { type: 'list_of_objects' },
        // add_trait / remove_trait accept string or object — left untyped.
      },
    },
    gender_filter: { type: ['string', 'null'] },
    worker_gender: { type: ['string', 'null'] },
    categories: { type: 'list_of_strings' },
    image: { type: ['string', 'null'] },
    nsfw: { type: 'bool' },
    stat_requirements: { type: 'dict_of_numbers' },
    specific_workers: { type: 'list_of_strings', catalog: 'all_worker_names' },
    specific_worker_images: { type: 'list_of_strings', catalog: 'all_worker_folders' },
    required_traits: { type: 'list_of_strings', catalog: 'all_traits' },
    excluded_traits: { type: 'list_of_strings', catalog: 'all_traits' },
    // Flag values are plain bools or { value, duration } objects.
    required_flags: { type: ['dict_of_bools', 'dict_of_objects'], key_catalog: 'all_event_flags' },
    excluded_flags: { type: ['dict_of_bools', 'dict_of_objects'], key_catalog: 'all_event_flags' },
    // Training interactions (advanced; edited as raw structures).
    training_skill: { type: ['string', 'null'] },
    training_pair: { type: ['string', 'null'] },
    training_branch_images: { type: 'object' },
    training_texts: { type: 'object' },
    training_results: { type: 'object' },
    training_insist_effects: { type: 'object' },
    training_intro_sequences: { type: 'object' },
    training_flow_ui: { type: 'object' },
    training_stat_preview: { type: 'object' },
  },
  rules: [
    {
      id: 'traits_exist',
      check: (e, ctx) =>
        allIn(ctx.catalogs.all_traits, e.required_traits)
        && allIn(ctx.catalogs.all_traits, e.excluded_traits),
      severity: 'error',
      message: 'required_traits/excluded_traits reference a trait that does not exist',
    },
    {
      id: 'effect_traits_exist',
      check: (e, ctx) => {
        const names = [];
        for (const k of ['add_trait', 'remove_trait']) {
          const v = e.effect?.[k];
          if (typeof v === 'string') names.push(v);
          else if (v && typeof v === 'object' && typeof v.name === 'string') names.push(v.name);
        }
        return allIn(ctx.catalogs.all_traits, names);
      },
      severity: 'warning',
      message: 'effect add_trait/remove_trait references a trait that does not exist',
    },
    {
      id: 'workers_exist',
      check: (e, ctx) => allIn(ctx.catalogs.all_worker_names, e.specific_workers),
      severity: 'warning',
      message: 'specific_workers lists a worker name not found in any workers file',
    },
    {
      id: 'gender_filter_known',
      check: (e) => e.gender_filter == null
        || ['male', 'female', 'lord', 'lady'].includes(e.gender_filter),
      severity: 'warning',
      message: 'gender_filter should be male, female, lord, or lady',
    },
  ],
  legacy: {},
};
