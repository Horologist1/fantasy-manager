// Event schema — game/data/events/*.json (array files; recruitment pool lives
// in events/recruit/ and has its own schema).
import { allIn, asList } from './_rules.js';

const STORE_VALUE_FIELDS = {
  var: { type: 'string', required: true },
  equals: { type: ['string', 'bool', 'int', 'float', 'null'] },
};

const PAGE_FIELDS = {
  text: { type: 'longtext', required: true },
  image: { type: ['string', 'null'] },
};

const TRAIT_EFFECT_FIELDS = {
  name: { type: ['string', 'null'], catalog: 'all_traits' },
  trait: { type: ['string', 'null'], catalog: 'all_traits' },
  duration: { type: 'int', min: 0 },
  target: { type: ['string', 'null'] },
};

const TRAIT_CHANCE_FIELDS = {
  trait: { type: ['string', 'null'], catalog: 'all_traits' },
  name: { type: ['string', 'null'], catalog: 'all_traits' },
  chance_percent: { type: 'float', min: 0, max: 100 },
  percent: { type: 'float', min: 0, max: 100 },
  duration: { type: 'int', min: 0 },
};

const EVENT_EFFECT_BRANCH_FIELDS = {
  money: { type: 'float' },
  reputation: { type: 'float' },
  joy: { type: 'float' },
  health: { type: 'float' },
  servant_health: { type: 'float' },
  energy: { type: 'float' },
  servant_energy: { type: 'float' },
  cost_modifier: { type: 'float' },
  custom: { type: ['string', 'null'] },
  item_id: { type: ['string', 'null'], catalog: 'all_items' },
  chance: { type: 'float', min: 0, max: 1 },
  consume_item: { type: ['string', 'null'], catalog: 'all_items' },
  recruit_worker: { type: 'bool' },
  event_flags: { type: 'dict_of_scalars', key_catalog: 'all_event_flags' },
  set_timestamp_flags: { type: 'list_of_strings', catalog: 'all_event_flags' },
  skill_modifiers: { type: 'dict_of_numbers', key_catalog: 'all_skills' },
  add_trait: {
    type: ['list_of_objects', 'object', 'string', 'list_of_strings', 'null'],
    item_fields: TRAIT_EFFECT_FIELDS,
    fields: TRAIT_EFFECT_FIELDS,
  },
  trait_chance: {
    type: ['list_of_objects', 'object', 'null'],
    item_fields: TRAIT_CHANCE_FIELDS,
    fields: TRAIT_CHANCE_FIELDS,
  },
  trait_remove_chance: {
    type: ['list_of_objects', 'object', 'null'],
    item_fields: TRAIT_CHANCE_FIELDS,
    fields: TRAIT_CHANCE_FIELDS,
  },
  add_attribute: {
    type: 'object',
    fields: {
      target: { type: ['string', 'null'] },
      joy: { type: 'float' },
      rebelliousness: { type: 'float' },
      romance: { type: 'float' },
      relationship: { type: 'float' },
      libido: { type: 'float' },
    },
  },
};

const EVENT_EFFECT_FIELDS = {
  ...EVENT_EFFECT_BRANCH_FIELDS,
  // Probability choices use random.random(), so authored values are 0.0–1.0.
  success_chance: { type: 'float', min: 0, max: 1 },
  relationship_bonus: { type: 'float' },
  random_worker: { type: 'bool' },
  worker_name: { type: ['string', 'null'], catalog: 'all_worker_names' },
  joy_worker_name: { type: ['string', 'null'], catalog: 'all_worker_names' },
  loot_rolls: { type: 'int', min: 0 },
  success: { type: 'object', fields: EVENT_EFFECT_BRANCH_FIELDS },
  failure: { type: 'object', fields: EVENT_EFFECT_BRANCH_FIELDS },
};

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
  effect_worker_filter: {
    type: 'object',
    fields: {
      required_active_professions: { type: 'list_of_strings', catalog: 'all_professions' },
      forbidden_active_professions: { type: 'list_of_strings', catalog: 'all_professions' },
      required_traits: { type: 'list_of_strings', catalog: 'all_traits' },
      excluded_traits: { type: 'list_of_strings', catalog: 'all_traits' },
    },
  },
  conditions: {
    type: 'object',
    fields: {
      start_when: { type: ['string', 'null'] },
      stop_when: { type: ['string', 'null'] },
    },
  },
  required_flags: { type: 'dict_of_bools' },
  excluded_flags: { type: 'dict_of_bools' },
  outcome_override: { type: ['string', 'null'] },
  image_skill: { type: ['string', 'null'], catalog: 'all_skills' },
  success_image: { type: ['string', 'null'] },
  message_pages: { type: 'list_of_objects', item_fields: PAGE_FIELDS },
  effect: { type: 'object', fields: EVENT_EFFECT_FIELDS },
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
  arc_id: { type: ['string', 'null'] },
  arc_stage: { type: ['int', 'null'], min: 0 },
  arc_kind: { type: ['string', 'null'] },
  worker_progress: {
    type: 'object',
    fields: {
      min_level: { type: 'float', min: 0 },
      min_stats: { type: 'dict_of_numbers' },
      min_skills: { type: 'dict_of_numbers', key_catalog: 'all_skills' },
      any_skills: { type: 'dict_of_numbers', key_catalog: 'all_skills' },
      required_traits: { type: 'list_of_strings', catalog: 'all_traits' },
    },
  },
  completion_timestamp_flag: { type: ['string', 'null'], catalog: 'all_event_flags' },
  description_pages: { type: 'list_of_objects', item_fields: PAGE_FIELDS },
  required_store_value: {
    type: ['list_of_objects', 'object', 'null'],
    item_fields: STORE_VALUE_FIELDS,
    fields: STORE_VALUE_FIELDS,
  },
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
  rules: EVENT_RULES,
  legacy: {},
};
