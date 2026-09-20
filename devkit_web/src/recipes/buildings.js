// Building recipes — new building type, add profession to an existing building.
import { slug, neutralConsequences } from './_helpers.js';

function makeStory(a, skillName) {
  const base = a.base_pay ?? 60;
  const name = a.profession_name || 'Worker';
  return {
    id: `${slug(a.profession_name || a.name || 'job')}_daily`,
    weight: 5,
    report: a.report || `Worked as ${name}`,
    description: null,
    difficulty_modifier: 0,
    worker_gender_requirement: null,
    player_gender_requirement: null,
    nsfw_only: false,
    skill_options: skillName ? [skillName] : [],
    event_image_skill_exclude: [],
    positive_traits: {},
    negative_traits: {},
    trait_msg_success: null,
    trait_msg_failure: null,
    trait_success: null,
    required_traits: [],
    excluded_traits: [],
    stat_requirements: {},
    descriptions: {
      failure: a.desc_failure || `{worker_name} struggles and gets nothing done.`,
      mediocre: a.desc_mediocre || `{worker_name} gets through the day without standing out.`,
      success: a.desc_success || `{worker_name} does solid work and customers are pleased.`,
      critical_success: a.desc_critical || `{worker_name} has an outstanding day — word spreads.`,
    },
    earnings: {
      failure: '0',
      mediocre: String(Math.round(base * 0.5)),
      success: String(base),
      critical_success: String(Math.round(base * 1.5)),
    },
    consequences: neutralConsequences(),
    story_image: null,
    failure_image: null,
    loot: { rolls: 0, bonus_items: [] },
  };
}

function makeProfession(a, skillName) {
  return {
    id: slug(a.profession_name),
    name: a.profession_name,
    description: a.profession_description || null,
    nsfw: !!a.nsfw,
    difficulty: a.difficulty || 'easy',
    skills: skillName ? [skillName] : [],
    max_daily_workers: a.max_daily_workers ?? 2,
    staffing_penalty: 1.0,
    staffing_bonus: 1.0,
    daily_story_count: { base: 1, bonus_formula: '0' },
    daily_stories: [makeStory(a, skillName)],
  };
}

export const simple_building_type_recipe = {
  id: 'simple_building_type',
  title: 'New Building Type',
  description: 'A complete new building with one job and a working daily story — playable immediately.',
  kind: 'building',
  default_output: 'buildings/buildings_<modname>.json',
  steps: [
    { id: 'name', type: 'string', label: 'Building name', required: true, hint: 'e.g. Bakery' },
    { id: 'skill_name', type: 'string', label: 'Building skill', required: true,
      hint: 'The skill workers roll here. Reuse an existing one (Charm, Service…) or invent one (Baking).' },
    { id: 'skill_description', type: 'string', label: 'Skill description',
      hint: 'Shown in the building UI.' },
    { id: 'locations', type: 'list_of_strings', catalog: 'all_map_locations',
      label: 'Allowed map locations', required: true,
      hint: 'Map slots where this building can be placed.' },
    { id: 'profession_name', type: 'string', label: 'Job name', required: true,
      hint: 'e.g. Baker' },
    { id: 'profession_description', type: 'string', label: 'Job description' },
    { id: 'difficulty', type: 'enum', label: 'Job difficulty',
      options: ['easy', 'medium', 'hard'], default: 'easy' },
    { id: 'max_daily_workers', type: 'int', label: 'Max workers in this job', default: 2, min: 1 },
    { id: 'base_pay', type: 'int', label: 'Earnings on a good day', default: 60, min: 0 },
    { id: 'report', type: 'string', label: 'Daily report line', required: true,
      hint: 'e.g. "Baked fresh bread"' },
    { id: 'desc_success', type: 'longtext', label: 'Daily story — success text',
      hint: 'Optional; a generic line is generated if empty. Use {worker_name}.' },
    { id: 'nsfw', type: 'bool', label: 'NSFW building?', default: false },
  ],
  build: (a) => ({
    id: slug(a.name),
    name: a.name,
    skill_name: a.skill_name,
    skill_description: a.skill_description || null,
    nsfw: !!a.nsfw,
    allowed_map_locations: a.locations || [],
    professions: [makeProfession(a, a.skill_name)],
  }),
};

export const add_profession_to_building_recipe = {
  id: 'add_profession_to_building',
  title: 'Add Job to Existing Building',
  description: 'Copies an existing building and adds your new job to it. Note: the game merges buildings by id, so your file replaces the base building — re-run this after game updates that change it.',
  kind: 'building',
  default_output: 'buildings/buildings_<modname>.json',
  steps: [
    {
      id: 'building', type: 'enum', label: 'Building', required: true,
      options: (ctx) => Object.keys(ctx.catalogs?.meta?.building_full || {}).sort(),
      option_descriptions: (ctx) => Object.fromEntries(
        Object.entries(ctx.catalogs?.meta?.building_full || {})
          .map(([id, b]) => [id, `${b.name} — jobs: ${(b.professions || []).map((p) => p.name).join(', ')}`]),
      ),
    },
    { id: 'profession_name', type: 'string', label: 'New job name', required: true },
    { id: 'profession_description', type: 'string', label: 'Job description' },
    {
      id: 'skill', type: 'enum', label: 'Skill used by the job',
      options: (ctx) => Array.from(ctx.catalogs?.all_skills || []).sort(),
    },
    { id: 'difficulty', type: 'enum', label: 'Job difficulty',
      options: ['easy', 'medium', 'hard'], default: 'easy' },
    { id: 'max_daily_workers', type: 'int', label: 'Max workers in this job', default: 2, min: 1 },
    { id: 'base_pay', type: 'int', label: 'Earnings on a good day', default: 60, min: 0 },
    { id: 'report', type: 'string', label: 'Daily report line', required: true },
    { id: 'desc_success', type: 'longtext', label: 'Daily story — success text',
      hint: 'Optional; a generic line is generated if empty. Use {worker_name}.' },
    { id: 'nsfw', type: 'bool', label: 'NSFW job?', default: false },
  ],
  build: (a, ctx) => {
    const full = ctx?.catalogs?.meta?.building_full?.[a.building];
    const building = full
      ? JSON.parse(JSON.stringify(full))
      : { id: a.building, name: a.building, skill_name: a.skill || '', professions: [] };
    building.professions = building.professions || [];
    building.professions.push(makeProfession(a, a.skill || building.skill_name));
    return building;
  },
};
