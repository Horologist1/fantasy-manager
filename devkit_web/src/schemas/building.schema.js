// Building type schema — game/data/buildings/*.json ({ building_types: [] }),
// merged by id at load time: a mod file with the same id fully overrides it.
import { allIn } from './_rules.js';

export const PROFESSION_FIELDS = {
  id: { type: 'string', required: true },
  name: { type: 'string', required: true },
  description: { type: ['string', 'null'] },
  nsfw: { type: 'bool' },
  difficulty: { type: ['string', 'null'] },
  skills: { type: 'list_of_strings' },
  max_daily_workers: { type: 'int', min: 0 },
  staffing_penalty: { type: 'float' },
  staffing_bonus: { type: 'float' },
  presence_roll_bonus: { type: 'int' },
  daily_story_count: {
    type: 'object',
    fields: {
      base: { type: 'int', min: 0 },
      bonus_formula: { type: ['formula', 'null'] },
    },
  },
  daily_stories: { type: 'list_of_objects' },
};

export const building_schema = {
  id: 'building',
  fields: {
    id: { type: 'string', required: true, unique_in_file: true },
    name: { type: 'string', required: true },
    skill_name: { type: 'string', required: true },
    skill_description: { type: ['string', 'null'] },
    nsfw: { type: 'bool' },
    allowed_map_locations: { type: 'list_of_strings' },
    show_in_manage_buildings: { type: 'bool' },
    professions: { type: 'list_of_objects', item_fields: PROFESSION_FIELDS },
  },
  rules: [
    {
      id: 'professions_present',
      check: (e) => Array.isArray(e.professions) && e.professions.length > 0,
      severity: 'warning',
      message: 'building has no professions — workers cannot be assigned to it',
    },
    {
      id: 'overrides_existing',
      check: (e, ctx) => !ctx.catalogs.all_buildings?.has(e.id),
      severity: 'warning',
      message: 'this id already exists — your file will fully override that building at load',
    },
    {
      id: 'profession_skills_exist',
      check: (e, ctx) => (e.professions || []).every(
        (p) => allIn(ctx.catalogs.all_skills, p.skills),
      ),
      severity: 'warning',
      message: 'a profession lists an unknown skill name',
    },
  ],
  legacy: {},
};
