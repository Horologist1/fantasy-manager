// Daily story schema — entries inside building professions' daily_stories and
// inside data/buildings/daily_story_extensions/*.json extension files.
import { allIn, OUTCOMES } from './_rules.js';

const CONSEQUENCE_FIELDS = {
  energy: { type: 'float' },
  health: { type: 'float' },
  joy: { type: 'float' },
  rebelliousness: { type: 'float' },
  romance: { type: 'float' },
  relationship: { type: 'float' },
  reputation: { type: 'float' },
  libido: { type: 'float' },
  obedience: { type: 'float' },
  trait_chance: { type: 'list_of_objects' },
  trait_remove_chance: { type: 'list_of_objects' },
  // give_item: string or { item_id, quantity } — left untyped.
};

function chanceTraits(e) {
  const out = [];
  for (const o of OUTCOMES) {
    const c = e.consequences?.[o];
    if (!c || typeof c !== 'object') continue;
    for (const k of ['trait_chance', 'trait_remove_chance']) {
      for (const t of c[k] || []) {
        const name = t && (t.trait || t.name);
        if (typeof name === 'string') out.push(name);
      }
    }
  }
  return out;
}

export const daily_story_schema = {
  id: 'daily_story',
  fields: {
    id: { type: 'string', required: true, unique_in_file: true },
    weight: { type: 'float', min: 0 },
    report: { type: ['string', 'null'] },
    description: { type: ['longtext', 'null'] },
    difficulty_modifier: { type: 'int' },
    worker_gender_requirement: { type: ['string', 'null'] },
    player_gender_requirement: { type: ['string', 'null'] },
    nsfw_only: { type: 'bool' },
    skill_options: { type: 'list_of_strings', catalog: 'all_skills' },
    event_image_skill_exclude: { type: 'list_of_strings' },
    image_fallback_patterns: { type: 'list_of_strings' },
    relevant_traits: { type: 'list_of_strings', catalog: 'all_traits' },
    positive_traits: { type: 'dict_of_numbers', key_catalog: 'all_traits' },
    negative_traits: { type: 'dict_of_numbers', key_catalog: 'all_traits' },
    trait_msg_success: { type: ['string', 'null'] },
    trait_msg_failure: { type: ['string', 'null'] },
    trait_success: { type: ['string', 'null'] },
    required_traits: { type: 'list_of_strings', catalog: 'all_traits' },
    excluded_traits: { type: 'list_of_strings', catalog: 'all_traits' },
    stat_requirements: { type: 'dict_of_numbers' },
    descriptions: {
      type: 'object',
      fields: Object.fromEntries(OUTCOMES.map((o) => [o, { type: ['string', 'null'] }])),
    },
    earnings: {
      type: 'object',
      fields: Object.fromEntries(OUTCOMES.map((o) => [o, { type: ['formula', 'float', 'null'] }])),
    },
    consequences: {
      type: 'object',
      fields: Object.fromEntries(
        OUTCOMES.map((o) => [o, { type: 'object', fields: CONSEQUENCE_FIELDS }]),
      ),
    },
    story_image: { type: ['string', 'null'] },
    failure_image: { type: ['string', 'null'] },
    loot: {
      type: 'object',
      fields: {
        rolls: { type: 'int', min: 0 },
        bonus_items: { type: ['list_of_strings', 'list_of_objects'] },
        monster_worker: { type: 'object' },
        captured_worker: { type: 'object' },
      },
    },
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
      id: 'trait_weight_keys_exist',
      check: (e, ctx) =>
        allIn(ctx.catalogs.all_traits, Object.keys(e.positive_traits || {}))
        && allIn(ctx.catalogs.all_traits, Object.keys(e.negative_traits || {})),
      severity: 'warning',
      message: 'positive_traits/negative_traits uses a trait name that does not exist',
    },
    {
      id: 'trait_chance_traits_exist',
      check: (e, ctx) => allIn(ctx.catalogs.all_traits, chanceTraits(e)),
      severity: 'warning',
      message: 'a trait_chance/trait_remove_chance entry references an unknown trait',
    },
    {
      id: 'skills_exist',
      check: (e, ctx) => allIn(ctx.catalogs.all_skills, e.skill_options),
      severity: 'warning',
      message: 'skill_options lists an unknown skill name',
    },
    {
      id: 'description_branches',
      check: (e) => !e.descriptions
        || OUTCOMES.every((o) => o in e.descriptions),
      severity: 'warning',
      message: 'descriptions is missing one of failure/mediocre/success/critical_success',
    },
    {
      id: 'earnings_branches',
      check: (e) => !e.earnings || OUTCOMES.every((o) => o in e.earnings),
      severity: 'warning',
      message: 'earnings is missing one of failure/mediocre/success/critical_success',
    },
  ],
  legacy: {},
};
