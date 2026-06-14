// Event schema — game/data/events/*.json (array files; recruitment pool lives
// in events/recruit/ and has its own schema).
import { allIn, asList } from './_rules.js';

export const CHOICE_FIELDS = {
  option: { type: 'string', required: true },
  condition: { type: ['string', 'null'] },
  threshold: { type: ['int', 'null'] },
  skill_check: { type: ['int', 'null'] },
  required_trait: { type: ['string', 'null'] },
  required_traits: { type: 'list_of_strings' },
  excluded_traits: { type: 'list_of_strings' },
  trait_visibility: { type: ['string', 'null'] },
  blocked_message: { type: ['string', 'null'] },
  message: { type: ['string', 'null'] },
  message_success: { type: ['string', 'null'] },
  message_failure: { type: ['string', 'null'] },
  message_failure_worker_effect_skipped: { type: ['string', 'null'] },
  restrict_worker_effects_to_filter: { type: 'bool' },
  effect_worker_filter: { type: 'object' },
  conditions: { type: 'object' },
  required_flags: { type: 'dict_of_bools' },
  excluded_flags: { type: 'dict_of_bools' },
  outcome_override: { type: ['string', 'null'] },
  effect: { type: 'object' },
};

function choiceTraits(e) {
  const out = [];
  for (const c of e.choices || []) {
    out.push(...(c.required_traits || []), ...(c.excluded_traits || []));
    if (typeof c.required_trait === 'string') out.push(c.required_trait);
  }
  return out;
}

export const EVENT_FIELDS = {
  id: { type: 'string', required: true, unique_in_file: true },
  description: { type: ['longtext', 'null'] },
  weight: { type: 'float', min: 0 },
  limited: { type: 'bool' },
  max_occurrences: { type: 'int', min: 0 },
  cooldown_days: { type: 'int', min: 0 },
  event_probability: { type: 'int', min: 0, max: 100 },
  guaranteed: { type: 'bool' },
  worker_name: { type: ['string', 'list_of_strings', 'null'] },
  specific_worker_images: { type: 'list_of_strings', catalog: 'all_worker_folders' },
  worker_selection: { type: ['string', 'null'] },
  worker_gender_requirement: { type: ['string', 'null'] },
  player_gender_requirement: { type: ['string', 'null'] },
  requires_assigned_worker: { type: 'bool' },
  required_building_worker_traits: { type: 'list_of_strings', catalog: 'all_traits' },
  required_active_professions: { type: 'list_of_strings', catalog: 'all_professions' },
  forbidden_active_professions: { type: 'list_of_strings', catalog: 'all_professions' },
  required_building_worker_min_skill: { type: ['int', 'null'] },
  required_building_worker_skill: { type: ['string', 'null'] },
  building_type: { type: ['list_of_strings', 'null'], catalog: 'all_buildings' },
  background_image: { type: ['string', 'null'] },
  success_image: { type: ['string', 'null'] },
  failure_image: { type: ['string', 'null'] },
  nsfw: { type: 'bool' },
  required_flags: { type: 'dict_of_bools', key_catalog: 'all_event_flags' },
  excluded_flags: { type: 'dict_of_bools', key_catalog: 'all_event_flags' },
  conditions: {
    type: 'object',
    fields: {
      start_when: { type: ['string', 'null'] },
      stop_when: { type: ['string', 'null'] },
    },
  },
  start_when: { type: ['string', 'null'] },
  stop_when: { type: ['string', 'null'] },
  event_music: { type: ['string', 'null'] },
  event_type: { type: ['string', 'null'] },
  _disabled: { type: ['string', 'null'] },
  choices: { type: 'list_of_objects', required: true, item_fields: CHOICE_FIELDS },
};

export const EVENT_RULES = [
  {
    id: 'choices_present',
    check: (e) => Array.isArray(e.choices) && e.choices.length > 0,
    severity: 'error',
    message: 'event needs at least one choice',
  },
  {
    id: 'traits_exist',
    check: (e, ctx) =>
      allIn(ctx.catalogs.all_traits, choiceTraits(e))
      && allIn(ctx.catalogs.all_traits, e.required_building_worker_traits),
    severity: 'error',
    message: 'a trait gate references a trait that does not exist in any traits file',
  },
  {
    id: 'buildings_exist',
    check: (e, ctx) => allIn(ctx.catalogs.all_buildings, asList(e.building_type)),
    severity: 'error',
    message: 'building_type references a building id that does not exist',
  },
  {
    id: 'professions_exist',
    check: (e, ctx) =>
      allIn(ctx.catalogs.all_professions, e.required_active_professions)
      && allIn(ctx.catalogs.all_professions, e.forbidden_active_professions),
    severity: 'error',
    message: 'required/forbidden_active_professions references an unknown profession id',
  },
  {
    id: 'skill_choice_needs_threshold',
    check: (e) => (e.choices || []).every((c) =>
      c.condition == null || c.condition === 'none'
      || typeof c.threshold === 'number' || typeof c.skill_check === 'number'),
    severity: 'warning',
    message: 'a skill-check choice has no threshold (the check cannot be resolved)',
  },
  {
    id: 'choice_required_trait_legacy',
    check: (e) => (e.choices || []).every((c) => c.required_trait == null),
    severity: 'warning',
    message: 'a choice uses legacy required_trait; prefer required_traits (list)',
  },
  {
    id: 'guaranteed_implies_weight_zero',
    check: (e) => !e.guaranteed || !e.weight,
    severity: 'warning',
    message: 'guaranteed events ignore weight; consider setting weight: 0',
  },
  {
    id: 'folders_exist',
    check: (e, ctx) => allIn(ctx.catalogs.all_worker_folders, e.specific_worker_images),
    severity: 'warning',
    message: 'specific_worker_images lists a folder not found under images/workers/',
  },
];

export const event_schema = {
  id: 'event',
  fields: EVENT_FIELDS,
  rules: [
    ...EVENT_RULES,
    {
      id: 'worker_gender_ignored',
      check: (e) => e.worker_gender_requirement == null,
      severity: 'warning',
      message: 'worker_gender_requirement is ignored by the random/building event pool',
    },
  ],
  legacy: {},
};
