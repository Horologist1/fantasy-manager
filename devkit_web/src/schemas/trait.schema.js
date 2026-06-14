// Trait schema — game/data/traits/*.json (array files, merged; first definition wins).
import { allIn } from './_rules.js';

export const trait_schema = {
  id: 'trait',
  fields: {
    name: { type: 'string', required: true, unique_in_file: true },
    conflicts: { type: 'list_of_strings', catalog: 'all_traits' },
    removes_traits: { type: 'list_of_strings', catalog: 'all_traits' },
    requires_traits: { type: 'list_of_strings', catalog: 'all_traits' },
    modifiers: {
      type: 'object',
      fields: {
        skill_modifiers: { type: 'dict_of_numbers', key_catalog: 'all_skills' },
        attribute_caps: { type: 'dict_of_numbers' },
        attribute_minimums: { type: 'dict_of_numbers' },
        daily_effects: { type: ['dict_of_numbers', 'dict_of_objects'] },
        earnings_multiplier: { type: 'float' },
        libido_max: { type: 'float' },
        libido_regeneration: { type: 'float' },
      },
    },
    duration: { type: 'int', min: 0 },
    only_assigned: { type: 'bool' },
    gender_restriction: { type: ['string', 'null'] },
    on_expire: { type: 'object' },
    reform_on_death: { type: 'bool' },
    skill_caps: { type: 'dict_of_numbers', key_catalog: 'all_skills' },
    // Some shipped traits carry these at top level (legacy placement);
    // daily_effects values may be numbers or {min, max} ranges.
    attribute_caps: { type: 'dict_of_numbers' },
    attribute_minimums: { type: 'dict_of_numbers' },
    daily_effects: { type: ['dict_of_numbers', 'dict_of_objects'] },
    description: { type: ['longtext', 'null'] },
    nsfw: { type: 'bool' },
  },
  rules: [
    {
      id: 'conflicts_exist',
      check: (e, ctx) => allIn(ctx.catalogs.all_traits, e.conflicts),
      severity: 'warning',
      message: 'conflicts lists a trait that does not exist in any traits file',
    },
    {
      id: 'removes_exist',
      check: (e, ctx) => allIn(ctx.catalogs.all_traits, e.removes_traits),
      severity: 'warning',
      message: 'removes_traits lists a trait that does not exist',
    },
    {
      id: 'requires_exist',
      check: (e, ctx) => allIn(ctx.catalogs.all_traits, e.requires_traits),
      severity: 'warning',
      message: 'requires_traits lists a trait that does not exist',
    },
    {
      id: 'skill_modifier_keys_exist',
      check: (e, ctx) =>
        allIn(ctx.catalogs.all_skills, Object.keys(e.modifiers?.skill_modifiers || {})),
      severity: 'warning',
      message: 'modifiers.skill_modifiers uses an unknown skill name',
    },
    {
      id: 'skill_cap_keys_exist',
      check: (e, ctx) => allIn(ctx.catalogs.all_skills, Object.keys(e.skill_caps || {})),
      severity: 'warning',
      message: 'skill_caps uses an unknown skill name',
    },
  ],
  legacy: {},
};
